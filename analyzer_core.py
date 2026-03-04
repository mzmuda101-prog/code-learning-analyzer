"""Core analysis logic for Code Learning Analyzer."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from analyzer_models import (
    AdvancedStats,
    COMMENT_PREFIXES,
    FileStats,
    LANGUAGE_BY_EXTENSION,
    LONG_LINE_LIMIT,
    SUPPORTED_EXTENSIONS,
    SummaryStats,
)

# Heurystyki do wykrywania deklaracji funkcji w popularnych jezykach.
# To nie jest parser AST, wiec celowo stawiamy na szybkie "wystarczajaco dobre" dopasowanie.
FUNCTION_PATTERNS = [
    re.compile(r"^\s*(?:async\s+)?def\s+\w+\s*\("),
    re.compile(r"^\s*function\s+\w+\s*\("),
    re.compile(r"^\s*(const|let|var)\s+\w+\s*=\s*(?:\([^)]*\)|\w+)\s*=>"),
    re.compile(r"^\s*(?!if\b|for\b|while\b|switch\b|catch\b)(?:async\s+)?[A-Za-z_]\w*\s*\([^)]*\)\s*\{"),
]

# Proste wzorce do przyblizonej oceny zlozonosci.
# Wnioski z tych metryk sa orientacyjne, ale przydatne do nauki i porownan miedzy plikami.
COMPLEXITY_PATTERNS = {
    "if_statements": re.compile(r"^\s*(if\s*\(|if\s+.+:|elif\s+.+:)"),
    "loops": re.compile(r"^\s*(for\s*\(|while\s*\(|for\s+.+:|while\s+.+:|do\s+while\s*\()"),
    "try_catch": re.compile(r"^\s*(try|catch|finally|except)\b"),
    "imports": re.compile(r"^\s*(import|from|require)\s+"),
    "classes": re.compile(r"^\s*(class|interface|struct)\s+\w+"),
}


def is_comment_line(line: str, suffix: str) -> bool:
    """Check if a line is a comment based on file extension."""
    stripped = line.strip()
    if not stripped:
        return False
    # Gdy rozszerzenie nie jest mapowane, domyslnie sprawdzamy najczestsze prefixy komentarzy.
    prefixes = COMMENT_PREFIXES.get(suffix, ["#", "//"])
    return any(stripped.startswith(prefix) for prefix in prefixes)


def _split_comment_and_code_lines(lines: list[str], suffix: str) -> tuple[int, int, list[tuple[int, str]]]:
    """Classify non-empty lines into comment/code with basic block comment support."""
    comment_lines = 0
    code_lines = 0
    code_line_details: list[tuple[int, str]] = []

    # Jezyki z komentarzami blokowymi /* ... */ obslugujemy recznie, linia po linii.
    c_style_suffixes = {".js", ".ts", ".java", ".c", ".cpp", ".cs", ".go", ".rs", ".php", ".css"}
    in_block_comment = False

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        # HTML traktujemy osobno, bo komentarze maja postac <!-- ... -->.
        if suffix == ".html":
            if in_block_comment:
                comment_lines += 1
                if "-->" in stripped:
                    in_block_comment = False
                continue
            if "<!--" in stripped:
                starts_with_comment = stripped.startswith("<!--")
                ends_comment = "-->" in stripped
                if starts_with_comment and (ends_comment or stripped.endswith("-->")):
                    comment_lines += 1
                    continue
                if starts_with_comment and not ends_comment:
                    in_block_comment = True
                    comment_lines += 1
                    continue

        # W stylu C liczymy caly blok jako komentarz, nawet gdy linia nie zaczyna sie od prefixu.
        if suffix in c_style_suffixes:
            if in_block_comment:
                comment_lines += 1
                if "*/" in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith("/*"):
                comment_lines += 1
                if "*/" not in stripped:
                    in_block_comment = True
                continue
            if stripped.startswith("*"):
                comment_lines += 1
                continue

        if is_comment_line(line, suffix):
            comment_lines += 1
        else:
            code_lines += 1
            code_line_details.append((line_num, stripped))

    return comment_lines, code_lines, code_line_details


def analyze_file(path: Path) -> FileStats:
    """Analyze a single file and return its statistics."""
    # Mini przewodnik (krok po kroku):
    # 1) Wczytaj plik i podziel go na linie.
    # 2) Rozdziel linie na kod/komentarze (_split_comment_and_code_lines).
    # 3) W jednym przebiegu policz: puste, dlugie, TODO i funkcje.
    # 4) Zloz wszystko do FileStats, zeby raporty mialy jeden wspolny format danych.
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    suffix = path.suffix.lower()

    total_lines = len(lines)
    empty_lines = 0
    comment_lines, code_lines, code_line_details = _split_comment_and_code_lines(lines, suffix)
    long_lines = 0
    todo_count = 0
    function_count = 0

    long_lines_details = []
    todo_details = []
    function_details = []

    # Funkcje wykrywamy tylko na liniach uznanych za kod, zeby nie liczyc komentarzy z "def/function".
    code_line_numbers = {line_num for line_num, _ in code_line_details}

    # Jedno przejscie po pliku liczy metryki "nauka-jakosc": dlugie linie, TODO i funkcje.
    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            empty_lines += 1
            continue

        if len(line) > LONG_LINE_LIMIT:
            long_lines += 1
            long_lines_details.append((line_num, line[:100] + "..." if len(line) > 100 else line))

        if "TODO" in line.upper():
            todo_count += 1
            todo_details.append((line_num, stripped))

        if line_num in code_line_numbers and any(pattern.search(line) for pattern in FUNCTION_PATTERNS):
            function_count += 1
            function_details.append((line_num, stripped))

    return FileStats(
        file=str(path),
        total_lines=total_lines,
        empty_lines=empty_lines,
        comment_lines=comment_lines,
        code_lines=code_lines,
        long_lines=long_lines,
        todo_count=todo_count,
        function_count=function_count,
        long_lines_details=long_lines_details,
        todo_details=todo_details,
        function_details=function_details,
    )


def analyze_advanced_stats(path: Path) -> AdvancedStats:
    """Analyze advanced code quality and complexity metrics for a file."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    suffix = path.suffix.lower()

    if_count = 0
    loop_count = 0
    try_catch_count = 0
    import_count = 0
    class_count = 0

    _, _, code_line_details = _split_comment_and_code_lines(lines, suffix)
    code_lines = [line for _, line in code_line_details]

    for _, line in code_line_details:
        stripped = line.strip()
        if COMPLEXITY_PATTERNS["if_statements"].search(stripped):
            if_count += 1
        if COMPLEXITY_PATTERNS["loops"].search(stripped):
            loop_count += 1
        if COMPLEXITY_PATTERNS["try_catch"].search(stripped):
            try_catch_count += 1
        if COMPLEXITY_PATTERNS["imports"].search(stripped):
            import_count += 1
        if COMPLEXITY_PATTERNS["classes"].search(stripped):
            class_count += 1

    # Uproszczona zlozonosc cyklomatyczna: 1 + punkty decyzji.
    # Nie pokrywa wszystkich konstrukcji jezykowych, ale dobrze pokazuje trend.
    cyclomatic_complexity = 1 + if_count + loop_count + try_catch_count
    total_lines = len(lines)
    code_density = len(code_lines) / total_lines if total_lines > 0 else 0
    duplication_score = _calculate_duplication_score(code_lines)

    return AdvancedStats(
        cyclomatic_complexity=cyclomatic_complexity,
        code_density=code_density,
        duplication_score=duplication_score,
        import_count=import_count,
        class_count=class_count,
        loop_count=loop_count,
        if_count=if_count,
        try_catch_count=try_catch_count,
    )


def _calculate_duplication_score(code_lines: list[str]) -> float:
    """Calculate a simple duplication score based on repeated patterns."""
    if len(code_lines) < 2:
        return 0.0

    # Normalizacja redukuje "szum" (np. inne liczby/stringi), aby lapac podobny ksztalt kodu.
    normalized_lines: list[str] = []
    for line in code_lines:
        if line in {"{", "}", "};"}:
            continue
        if line.startswith(("import ", "from ", "#include", "using ")):
            continue

        normalized = re.sub(r'"[^"]*"|\'[^\']*\'', '"STR"', line)
        normalized = re.sub(r"\b\d+\b", "NUM", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip().lower()
        if len(normalized) >= 16:
            normalized_lines.append(normalized)

    if not normalized_lines:
        return 0.0

    line_counts: dict[str, int] = {}
    for line in normalized_lines:
        line_counts[line] = line_counts.get(line, 0) + 1

    duplicate_instances = sum(count - 1 for count in line_counts.values() if count > 1)
    # Wynik 0..1: 0 = brak widocznych powtorek, 1 = bardzo duzo duplikatow.
    return min(duplicate_instances / len(normalized_lines), 1.0)


def collect_files(path: Path, recursive: bool = True) -> list[Path]:
    """Collect all supported files from a directory (optionally recursively)."""
    # Dla pojedynczego poprawnego pliku zwracamy liste 1-elementowa, by uproscic dalszy pipeline.
    if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
        return [path]
    if path.is_file():
        return []

    # "**/*" schodzi po podkatalogach, "*" bierze tylko pierwszy poziom.
    pattern = "**/*" if recursive else "*"
    files: list[Path] = []
    for candidate in path.glob(pattern):
        if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(candidate)
    return sorted(files)


def summarize(results: Iterable[FileStats]) -> SummaryStats:
    """Create summary statistics from multiple FileStats objects."""
    stats_list = list(results)
    return SummaryStats(
        files_count=len(stats_list),
        total_lines=sum(x.total_lines for x in stats_list),
        empty_lines=sum(x.empty_lines for x in stats_list),
        comment_lines=sum(x.comment_lines for x in stats_list),
        code_lines=sum(x.code_lines for x in stats_list),
        long_lines=sum(x.long_lines for x in stats_list),
        todo_count=sum(x.todo_count for x in stats_list),
        function_count=sum(x.function_count for x in stats_list),
    )


def build_advanced_stats_map(results: list[FileStats]) -> dict[str, AdvancedStats]:
    """Precompute advanced stats for each analyzed file."""
    return {item.file: analyze_advanced_stats(Path(item.file)) for item in results}


def language_usage_stats(results: list[FileStats]) -> list[dict[str, int | float | str]]:
    """Aggregate language usage by file extension.

    Returns a list sorted by code lines desc:
    [{"language": str, "files": int, "code_lines": int, "code_share": float}]
    """
    # "or 1" zabezpiecza przed dzieleniem przez zero przy pustym kodzie.
    total_code_lines = sum(item.code_lines for item in results) or 1
    usage: dict[str, dict[str, int]] = {}

    for item in results:
        suffix = Path(item.file).suffix.lower()
        # Gdy rozszerzenie nieznane, budujemy czytelna etykiete fallback.
        language = LANGUAGE_BY_EXTENSION.get(suffix, suffix.lstrip(".").upper() or "Unknown")
        if language not in usage:
            usage[language] = {"files": 0, "code_lines": 0}
        usage[language]["files"] += 1
        usage[language]["code_lines"] += item.code_lines

    rows = [
        {
            "language": language,
            "files": values["files"],
            "code_lines": values["code_lines"],
            "code_share": values["code_lines"] / total_code_lines,
        }
        for language, values in usage.items()
    ]
    return sorted(rows, key=lambda item: (int(item["code_lines"]), int(item["files"])), reverse=True)


def learning_tips(summary: SummaryStats, results: list[FileStats]) -> list[str]:
    """Generate learning tips based on code analysis summary."""
    tips: list[str] = []
    if not results:
        return ["Brak danych do analizy. Dodaj przynajmniej jeden obslugiwany plik."]

    # Pracujemy na proporcjach, bo sa bardziej porownywalne miedzy malym i duzym projektem.
    code_lines = max(summary.code_lines, 1)
    comment_ratio = summary.comment_lines / code_lines
    long_line_ratio = summary.long_lines / code_lines

    advanced_stats_map = build_advanced_stats_map(results)
    # Laczymy statystyki bazowe i zaawansowane per plik, zeby tworzyc bardziej precyzyjne porady.
    advanced_by_file = [(item, advanced_stats_map[item.file]) for item in results]
    avg_complexity = sum(adv.cyclomatic_complexity for _, adv in advanced_by_file) / len(advanced_by_file)
    avg_complexity_per_100 = (
        sum((adv.cyclomatic_complexity / max(item.code_lines, 1)) * 100 for item, adv in advanced_by_file)
        / len(advanced_by_file)
    )
    worst_complexity_file, worst_complexity_adv = max(
        advanced_by_file,
        key=lambda pair: pair[1].cyclomatic_complexity,
    )
    worst_complexity_density_file, worst_complexity_density_adv = max(
        advanced_by_file,
        key=lambda pair: pair[1].cyclomatic_complexity / max(pair[0].code_lines, 1),
    )
    worst_dup_file, worst_dup_adv = max(
        advanced_by_file,
        key=lambda pair: pair[1].duplication_score,
    )

    # Progi sa pragmatyczne (learning-oriented), a nie akademickie.
    # Ich celem jest wskazanie kolejnych krokow nauki, nie "ocena koncowa".
    # Warunek ">= 40 linii kodu" zmniejsza ryzyko falszywych alarmow dla mini-plikow.
    if comment_ratio < 0.08 and summary.code_lines >= 40:
        tips.append(
            f"Komentarze to tylko {comment_ratio:.1%} linii kodu. Dodaj krótkie komentarze do trudniejszych fragmentów (cel: 10-20%)."
        )

    if long_line_ratio > 0.08:
        file_with_long_lines = max(results, key=lambda item: item.long_lines)
        file_name = Path(file_with_long_lines.file).name
        tips.append(
            f"Masz duzo dlugich linii ({summary.long_lines}, czyli {long_line_ratio:.1%} kodu). Zacznij od pliku {file_name}."
        )
        if file_with_long_lines.long_lines_details:
            line_num, _ = file_with_long_lines.long_lines_details[0]
            tips.append(
                f"Pierwszy konkretny cel: podziel dluga linie w {file_name}:{line_num} na 2-3 krotsze kroki."
            )

    if summary.function_count == 0 and summary.code_lines > 20:
        tips.append("Brak funkcji przy wiekszym pliku. Wydziel 2-3 funkcje pomocnicze, zeby cwiczyc modularnosc.")
    elif summary.function_count > 0:
        # Metryka "linie na funkcje" dobrze wychwytuje zbyt duze, wielozadaniowe funkcje.
        lines_per_function = summary.code_lines / summary.function_count
        if lines_per_function > 60:
            tips.append(
                f"Srednio {lines_per_function:.1f} linii na funkcje. Sprobuj dzielic funkcje >40 linii na mniejsze fragmenty."
            )

    # Tu patrzymy jednoczesnie na srednia projektu i najgorszy przypadek, zeby nie przeoczyc "hotspotu".
    worst_density = (worst_complexity_density_adv.cyclomatic_complexity / max(worst_complexity_density_file.code_lines, 1)) * 100
    if avg_complexity_per_100 > 8 or worst_density > 12:
        tips.append(
            f"Najtrudniejszy plik na jednostke kodu to {Path(worst_complexity_density_file.file).name} ({worst_density:.1f} punktow zlozonosci / 100 linii). Ogranicz zagniezdzenia if/for."
        )
    elif avg_complexity > 25 or worst_complexity_adv.cyclomatic_complexity > 40:
        tips.append(
            f"Najwyzsza zlozonosc ma {Path(worst_complexity_file.file).name} ({worst_complexity_adv.cyclomatic_complexity})."
        )

    if worst_dup_adv.duplication_score > 0.18:
        tips.append(
            f"Wysoka duplikacja w {Path(worst_dup_file.file).name} ({worst_dup_adv.duplication_score:.1%}). Wyodrebnij powtarzany kod do funkcji."
        )

    if summary.todo_count == 0:
        tips.append("Dodaj 2-3 TODO jako mini-plan nauki (najpierw bugfix, potem refactor, na koncu test).")
    elif summary.todo_count > 12:
        tips.append("Masz duzo TODO. Zamknij najstarsze 3 i zamien je na konkretne zadania z data.")

    # Minimalna liczba porad sprawia, ze raport zawsze daje konkretny nastepny krok.
    if len(tips) < 3:
        tips.append("Dobry poziom bazowy. Kolejny krok: dopisz testy jednostkowe dla 2 najwazniejszych funkcji.")

    return tips[:8]


def metric_explanations() -> list[str]:
    """Return short learning-oriented explanations for core metrics."""
    return [
        f"Linie > {LONG_LINE_LIMIT}: im mniej, tym lepiej dla czytelnosci; cel: <5-10% linii kodu.",
        "Gestosc kodu: procent linii, ktore sa realnym kodem (bez pustych i bez komentarzy).",
        "Zlozonosc cyklomatyczna: orientacyjna liczba sciezek decyzji (if/for/while/except).",
        "Zlozonosc / 100 linii: pozwala porownac trudnosc miedzy malym i duzym plikiem.",
        "Wspolczynnik duplikacji: ile podobnych linii kodu sie powtarza.",
        "TODO: lista swiadomych rzeczy do poprawy; dobre do planu nauki.",
    ]
