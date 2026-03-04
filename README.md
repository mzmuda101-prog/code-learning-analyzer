# Code Learning Analyzer

Uniwersalny, otwartoźródłowy analizator jakości kodu – skierowany do osób uczących się programowania, junior developerów, rekruterów technicznych oraz wszystkich, którzy chcą szybciej poprawić jakość swojego kodu na realnych projektach.

> Repozytorium publiczne – referencja do CV lub na LinkedIn.  
> Demo oraz przykładowe raporty znajdziesz poniżej (sekcja **Demo**).

---

## O projekcie

Code Learning Analyzer pomaga ocenić kod nie tylko pod względem liczbowym (linie, funkcje, TODO, złożoność), ale także podpowiada:
- co poprawiać w pierwszej kolejności,
- dlaczego te elementy są istotne,
- jak poprawić jakość Twoich projektów na GitHubie.

Celem jest mniej “vibecodingu”, a więcej pracy świadomej, rozwijającej dobre nawyki inżynierskie.

---

## Najważniejsze funkcje

- **Analiza plików i folderów** – rekurencyjna oraz jednowarstwowa
- **Wieloplatformowe raporty**:  
  - raport tekstowy (`.txt`),  
  - raport Excel (`.xlsx`),  
  - raport PDF ze zintegrowanymi wykresami (`.pdf`),  
  - raport HTML (`.html`).
- **Zaawansowane statystyki Git** – analiza historii zmian, wykresy aktywności
- **Podsumowanie udziału języków** – informacja ile kodu w danym języku, wykresy dla projektów wielojęzykowych
- **Tryb nauki i wyjaśnienia metryk** (`--explain-metrics` w CLI, checkbox w GUI) – idealne do nauki analizowania kodu, szczególnie dla osób na poziomie juniora
- **Dedykowane rekomendacje rozwojowe** – sekcja “co warto ćwiczyć dalej” generowana na podstawie analizy
- **Obsługa wielu rozszerzeń plików, łatwe dostosowywanie do własnych potrzeb**

---

## Przykładowa analiza (Demo)

Na razie repozytorium **nie zawiera** gotowych plików demo – zamiast martwych linków możesz sam szybko wygenerować raporty, żeby zobaczyć jak to wygląda w praktyce.

- **Raport HTML** (łatwo podejrzeć w przeglądarce):

```bash
python3 analyzer.py /sciezka/do/projektu --html raport_demo.html --html-top-languages
```

- **Raport PDF z wykresami**:

```bash
python3 analyzer.py /sciezka/do/projektu --pdf raport_demo.pdf
```

Po wygenerowaniu możesz dodać własne przykładowe pliki (np. do folderu `demo/`) i podlinkować je w tym README, jeśli chcesz mieć w repo statyczne przykłady.

---

## Szybki start

1. **Klonowanie repo:**  
    ```bash
    git clone https://github.com/mateuszuser/code-learning-analyzer.git
    cd code-learning-analyzer
    ```
2. **Analiza z terminala:**  
    ```bash
    python3 analyzer.py ./ścieżka/do/projektu
    ```
    Wybrane opcje:
    ```bash
    python3 analyzer.py ./sciezka --out a.txt           # raport tekstowy
    python3 analyzer.py ./sciezka --xlsx a.xlsx         # raport Excel
    python3 analyzer.py ./sciezka --pdf a.pdf           # PDF z wykresami
    python3 analyzer.py ./sciezka --html a.html         # HTML
    python3 analyzer.py ./sciezka --no-recursive        # bez podfolderów
    python3 analyzer.py ./sciezka --explain-metrics     # tryb nauki (wyjaśnienia)
    python3 analyzer.py ./sciezka --git --git-start "4 weeks ago" --git-end "now"
    ```
3. **Uruchomienie GUI:**  
    ```bash
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

## Licencja

MIT (zobacz plik `LICENSE`).
