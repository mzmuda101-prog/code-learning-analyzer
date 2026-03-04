# Code Learning Analyzer v2

Prosty analizator kodu napisany pod nauke programowania.
Cel projektu: mniej "vibecodingu", wiecej rozumienia jakosci kodu i swiadomych decyzji.

## Dlaczego ten projekt

To narzedzie zamienia surowe liczby (linie, funkcje, TODO, zlozonosc) na konkretne podpowiedzi:
- co poprawic najpierw,
- dlaczego to wazne,
- od jakiego pliku/linii zaczac.

Projekt jest przygotowywany jako element portfolio GitHub/CV.

## Najwazniejsze funkcje

- analiza pliku lub folderu (rekurencyjnie lub nie),
- raport tekstowy (`.txt`),
- raport Excel (`.xlsx`),
- raport PDF z wykresami (`.pdf`),
- raport HTML (`.html`),
- analiza Git (aktywność zmian),
- analiza użycia języków (udział kodu per język),
- tryb nauki: wyjasnienie metryk (`--explain-metrics` / checkbox w GUI).

## Szybki start (CLI)

```bash
cd /Users/mateuszuser/Programistyka/code-learning-analyzer
python3 analyzer.py /sciezka/do/folderu
```

Najczesciej uzywane opcje:

```bash
# raport txt
python3 analyzer.py /sciezka/do/folderu --out raport.txt

# raport xlsx
python3 analyzer.py /sciezka/do/folderu --xlsx raport.xlsx

# raport pdf
python3 analyzer.py /sciezka/do/folderu --pdf raport.pdf

# raport html
python3 analyzer.py /sciezka/do/folderu --html raport.html

# raport html: top 5 jezykow + bezpiecznik wydajnosci
python3 analyzer.py /sciezka/do/folderu --html raport.html --html-top-languages

# bez podfolderow
python3 analyzer.py /sciezka/do/folderu --no-recursive

# objasnienia metryk (nauka)
python3 analyzer.py /sciezka/do/folderu --explain-metrics

# analiza Git z zakresem dat
python3 analyzer.py /sciezka/do/folderu --git --git-start "1 month ago" --git-end "now"
```

## GUI

```bash
cd /Users/mateuszuser/Programistyka/code-learning-analyzer
python3 gui.py
```

W GUI mozna:
- wybrac plik/folder,
- wlaczyc rekurencje,
- zaznaczyc szczegolowe statystyki,
- wlaczyc "Wyjasnij metryki (tryb nauki)",
- wygenerowac raporty (`txt/xlsx/pdf/html`).

## Jak czytac raport

Raport pokazuje m.in.:
- liczbe plikow i linii,
- linie kodu, komentarzy i puste,
- liczbe funkcji i TODO,
- dlugie linie (`>100`),
- zlozonosc cyklomatyczna,
- zlozonosc na 100 linii kodu,
- wspolczynnik duplikacji,
- rekomendacje "co cwiczyc dalej".

## Testy

Projekt ma testy jednostkowe (`unittest`), bez dodatkowych bibliotek:

```bash
cd /Users/mateuszuser/Programistyka/code-learning-analyzer
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Wymagania opcjonalne

- Excel: `python3 -m pip install openpyxl`
- PDF/wykresy/HTML/Git report: `python3 -m pip install matplotlib reportlab`

## Obslugiwane rozszerzenia

`.py .js .ts .java .c .cpp .cs .go .rs .php .sh .html .css`

## Struktura projektu

- `analyzer.py` - CLI i punkt startowy (spina moduly)
- `analyzer_core.py` - logika analizy i metryki
- `analyzer_reports.py` - budowanie raportow i eksporty (`txt/xlsx/pdf/html`)
- `analyzer_git.py` - analiza historii Git i wykres Git
- `analyzer_models.py` - modele danych i stale projektu
- `gui.py` - interfejs Tkinter
- `tests/test_analyzer.py` - testy jednostkowe

## Roadmapa rozwoju

1. Rozbicie na moduly (`core`, `reports`, `git`) - zrobione.
2. Dodac benchmarki i prosty profil wydajnosci.
3. Dodac wersje `pytest` + CI po wrzutce na GitHub.
4. Dodac porownanie "postepu w czasie" miedzy kolejnymi raportami.

## Publikacja na GitHub (checklista)

1. Uruchom testy lokalnie i sprawdz, ze wszystko jest zielone.
2. Upewnij sie, ze pliki wynikowe raportow nie ida do repo (`.gitignore`).
3. Dodaj 2-3 screenshoty GUI/raportu do `README` (sekcja "Demo").
4. W opisie repo dodaj: "learning-focused code analyzer with CLI + GUI".
5. Po publikacji dopisz link do repo w CV/portfolio.

## Licencja

MIT (zobacz plik `LICENSE`).
