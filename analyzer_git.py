"""Git-related analysis helpers for Code Learning Analyzer."""

from __future__ import annotations

from pathlib import Path


def _find_git_repo(path: Path) -> Path | None:
    """Find nearest Git repository for a file or directory path."""
    start_path = path if path.is_dir() else path.parent
    # Idziemy od biezacej sciezki do katalogow nadrzednych, az trafimy na .git.
    for candidate in [start_path, *start_path.parents]:
        if (candidate / ".git").exists():
            return candidate
    return None


def analyze_git_changes(path: Path, start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    """Analyze code changes over time using Git history."""
    import subprocess

    try:
        # Szybka walidacja, czy komenda git jest dostepna zanim zaczniemy analize.
        subprocess.run(["git", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError("Git nie jest zainstalowany lub nie jest dostępny w PATH.") from exc

    repo_path = _find_git_repo(path)
    if repo_path is None:
        raise RuntimeError(f"Podana sciezka nie znajduje sie w repozytorium Git: {path}")

    try:
        # Zakres dat jest opcjonalny: gdy go podamy, git ogranicza log do wskazanego okna czasu.
        cmd = ["git", "log", "--pretty=format:%H|%an|%ad|%s", "--date=short"]
        if start_date:
            cmd.extend(["--since", start_date])
        if end_date:
            cmd.extend(["--until", end_date])

        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, check=True)
        git_log = result.stdout.strip()
        if not git_log:
            return []

        commits = []
        for line in git_log.split("\n"):
            if "|" not in line:
                continue

            commit_hash, author, date, message = line.split("|", 3)
            # Korzystamy z --stat (a nie pelnego diffa), bo potrzebujemy zgrubnych metryk per commit.
            stats_cmd = ["git", "show", "--stat", "--format=", commit_hash]
            stats_result = subprocess.run(stats_cmd, cwd=repo_path, capture_output=True, text=True, check=True)

            lines_added = 0
            lines_removed = 0
            files_changed = 0

            # Parsujemy tylko linie podsumowania typu "X files changed, Y insertions(+), Z deletions(-)".
            for stat_line in stats_result.stdout.split("\n"):
                stat_line = stat_line.strip()
                if "files changed" not in stat_line:
                    continue

                parts = stat_line.split(",")
                files_changed = int(parts[0].split()[0])
                for part in parts[1:]:
                    part = part.strip()
                    if "insertions" in part:
                        lines_added = int(part.split()[0])
                    elif "deletions" in part:
                        lines_removed = int(part.split()[0])

            commits.append(
                {
                    "hash": commit_hash,
                    "author": author,
                    "date": date,
                    "message": message,
                    "files_changed": files_changed,
                    "lines_added": lines_added,
                    "lines_removed": lines_removed,
                    "net_change": lines_added - lines_removed,
                }
            )

        return commits
    except subprocess.CalledProcessError as exc:
        # stderr z gita bywa bardzo pomocny przy diagnozie (np. zly format daty).
        raise RuntimeError(f"Blad podczas analizy Git: {exc.stderr}") from exc


def create_git_report(path: Path, commits: list[dict], out_path: Path) -> None:
    """Create a Git analysis report chart."""
    try:
        import matplotlib
        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
        from datetime import datetime
    except ImportError as exc:
        raise RuntimeError(
            "Brak biblioteki matplotlib. Zainstaluj: python3 -m pip install matplotlib"
        ) from exc

    if not commits:
        # Przy braku commitow zapisujemy prosty raport tekstowy, zeby uzytkownik dostal jasny komunikat.
        with open(out_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(f"=== Analiza zmian Git - {path.name} ===\n")
            file_handle.write("Brak commitów do analizy w podanym zakresie czasu.\n")
        return

    dates = [datetime.strptime(commit["date"], "%Y-%m-%d") for commit in commits]
    lines_added = [commit["lines_added"] for commit in commits]
    lines_removed = [commit["lines_removed"] for commit in commits]
    net_changes = [commit["net_change"] for commit in commits]
    authors = [commit["author"] for commit in commits]

    # 4 wykresy: trend dodan/usuniec, zmiana netto, udzial autorow i rozklad liczby zmienionych plikow.
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(f"Analiza zmian Git - {path.name}", fontsize=16, fontweight="bold")

    ax1.plot(dates, lines_added, "g-", label="Dodane linie", linewidth=2)
    ax1.plot(dates, lines_removed, "r-", label="Usuniete linie", linewidth=2)
    ax1.fill_between(dates, lines_added, alpha=0.3, color="green")
    ax1.fill_between(dates, lines_removed, alpha=0.3, color="red")
    ax1.set_title("Linie dodane/usuniete w czasie", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Liczba linii")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.bar(range(len(net_changes)), net_changes, color=["green" if value > 0 else "red" for value in net_changes], alpha=0.7)
    ax2.set_title("Zmiany netto (dodane - usuniete)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Zmiana netto")
    ax2.set_xlabel("Commity")
    ax2.grid(True, alpha=0.3)

    from collections import Counter

    author_counts = Counter(authors)
    ax3.pie(list(author_counts.values()), labels=list(author_counts.keys()), autopct="%1.1f%%", startangle=90)
    ax3.set_title("Aktywnosc autorow", fontsize=12, fontweight="bold")

    files_changed = [commit["files_changed"] for commit in commits]
    ax4.hist(files_changed, bins=range(min(files_changed), max(files_changed) + 2), alpha=0.7, color="blue", edgecolor="black")
    ax4.set_title("Rozklad zmienionych plikow", fontsize=12, fontweight="bold")
    ax4.set_xlabel("Liczba zmienionych plikow")
    ax4.set_ylabel("Liczba commitów")
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
