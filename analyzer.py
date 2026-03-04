#!/usr/bin/env python3
"""CLI entrypoint and compatibility facade for Code Learning Analyzer."""

from __future__ import annotations

import argparse
from pathlib import Path

from analyzer_core import (
    analyze_advanced_stats,
    analyze_file,
    build_advanced_stats_map,
    collect_files,
    language_usage_stats,
    learning_tips,
    metric_explanations,
    summarize,
)
from analyzer_git import analyze_git_changes, create_git_report
from analyzer_models import SUPPORTED_EXTENSIONS
from analyzer_reports import (
    build_report,
    create_html_report,
    create_visualization_report,
    write_xlsx_report,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the code analyzer."""
    parser = argparse.ArgumentParser(
        description="Prosty analizator kodu (v2): plik/folder + raport txt."
    )

    parser.add_argument("path", help="Sciezka do pliku albo folderu")
    parser.add_argument("--out", dest="out_path", help="Opcjonalna sciezka do zapisu raportu .txt")
    parser.add_argument("--xlsx", dest="xlsx_path", help="Opcjonalna sciezka do zapisu raportu .xlsx")
    parser.add_argument("--pdf", dest="pdf_path", help="Opcjonalna sciezka do zapisu raportu wizualizacji .pdf")
    parser.add_argument("--no-recursive", action="store_true", help="Dla folderu: analizuj tylko pierwszy poziom")

    parser.add_argument("--git", action="store_true", help="Wlacz analize zmian w czasie (wymaga repozytorium Git)")
    parser.add_argument(
        "--git-start",
        dest="git_start",
        help="Poczatek zakresu czasu dla analizy Git (np. '1 month ago', '2024-01-01')",
    )
    parser.add_argument(
        "--git-end",
        dest="git_end",
        help="Koniec zakresu czasu dla analizy Git (np. 'now', '2024-12-31')",
    )

    parser.add_argument("--html", dest="html_path", help="Opcjonalna sciezka do zapisu raportu HTML")
    parser.add_argument(
        "--html-top-languages",
        action="store_true",
        help="W raporcie HTML pokazuj tylko top 5 jezykow (reszta jako 'Inne')",
    )
    parser.add_argument(
        "--html-safe-mode",
        dest="html_safe_mode",
        action="store_true",
        default=True,
        help="Tryb wydajnosci HTML (domyslnie wlaczony)",
    )
    parser.add_argument(
        "--html-no-safe-mode",
        dest="html_safe_mode",
        action="store_false",
        help="Wylacz tryb wydajnosci HTML",
    )
    parser.add_argument(
        "--explain-metrics",
        action="store_true",
        help="Dodaj sekcje objasniajaca jak interpretowac metryki",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for the code analyzer."""
    args = parse_args()
    path = Path(args.path).expanduser().resolve()

    if not path.exists():
        print(f"Blad: sciezka nie istnieje: {path}")
        return 1

    files = collect_files(path, recursive=not args.no_recursive)
    if not files:
        print("Blad: nie znaleziono plikow do analizy.")
        print(f"Obslugiwane rozszerzenia: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
        return 1

    results = [analyze_file(file_path) for file_path in files]
    report = build_report(path, results, explain_metrics=args.explain_metrics)
    print(report)

    if args.out_path:
        out_path = Path(args.out_path).expanduser().resolve()
        out_path.write_text(report + "\n", encoding="utf-8")
        print(f"\nZapisano raport do: {out_path}")

    if args.xlsx_path:
        xlsx_path = Path(args.xlsx_path).expanduser().resolve()
        try:
            write_xlsx_report(path, results, xlsx_path)
        except RuntimeError as exc:
            print(f"Blad: {exc}")
            return 1
        print(f"Zapisano raport XLSX do: {xlsx_path}")

    if args.pdf_path:
        pdf_path = Path(args.pdf_path).expanduser().resolve()
        try:
            create_visualization_report(path, results, pdf_path)
        except RuntimeError as exc:
            print(f"Blad: {exc}")
            return 1
        print(f"Zapisano raport wizualizacji PDF do: {pdf_path}")

    if args.git:
        try:
            print("\n=== Analiza zmian Git ===")
            commits = analyze_git_changes(path, args.git_start, args.git_end)

            if commits:
                print(f"Znaleziono {len(commits)} commitów do analizy.")

                git_chart_path = path.parent / f"{path.name}_git_analysis.png"
                create_git_report(path, commits, git_chart_path)
                print(f"Zapisano wykres analizy Git: {git_chart_path}")

                total_added = sum(item["lines_added"] for item in commits)
                total_removed = sum(item["lines_removed"] for item in commits)
                total_files = sum(item["files_changed"] for item in commits)

                print(f"Łączne zmiany: +{total_added} -{total_removed} (netto: {total_added - total_removed})")
                print(f"Łącznie zmienionych plików: {total_files}")
            else:
                print("Brak commitów do analizy w podanym zakresie czasu.")

        except RuntimeError as exc:
            print(f"Blad analizy Git: {exc}")
            return 1

    if args.html_path:
        html_path = Path(args.html_path).expanduser().resolve()
        try:
            if args.html_safe_mode:
                create_html_report(
                    path,
                    results,
                    html_path,
                    top_languages_only=args.html_top_languages,
                    max_languages=12,
                    max_quality_rows=300,
                    max_file_rows=600,
                )
            else:
                create_html_report(
                    path,
                    results,
                    html_path,
                    top_languages_only=args.html_top_languages,
                    max_languages=200,
                    max_quality_rows=5000,
                    max_file_rows=5000,
                )
            print(f"Zapisano raport HTML do: {html_path}")
        except RuntimeError as exc:
            print(f"Blad: {exc}")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
