#!/usr/bin/env python3
"""Tkinter GUI for analyzer v2 — improved UX."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import analyzer

# ---------------------------------------------------------------------------
# Minimalny helper tooltipa (poprawka kosmetyczna)
# ---------------------------------------------------------------------------

class _ToolTip:
    """Lekki balonowy tooltip pokazywany na hover."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        """Inicjalizuje tooltip do widgetu."""
        self._widget = widget
        self._text = text
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event: object = None) -> None:
        """Pokazuje dymek z tekstem nad widgetem."""
        x = self._widget.winfo_rootx() + 12
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 6
        self._tip = tk.Toplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self._tip,
            text=self._text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("TkDefaultFont", 9),
            wraplength=320,
            justify="left",
            padx=6,
            pady=4,
        )
        label.pack()

    def _hide(self, _event: object = None) -> None:
        """Ukrywa dymek tooltipa."""
        if self._tip:
            self._tip.destroy()
            self._tip = None

def _tip(widget: tk.Widget, text: str) -> _ToolTip:
    """Przypina tooltip z podanym tekstem do widgetu."""
    return _ToolTip(widget, text)

# ---------------------------------------------------------------------------
# Glowna aplikacja
# ---------------------------------------------------------------------------

class AnalyzerApp:
    """Main application class for the Code Learning Analyzer GUI."""

    def __init__(self, root: tk.Tk) -> None:
        """Tworzy interfejs oraz inicjalizuje zmienne i wywołuje budowanie UI."""
        self.root = root
        self.root.title("Code Learning Analyzer v2")
        self.root.geometry("980x750")
        self.root.minsize(820, 600)
        self.root.configure(bg="#f3f4f6")

        # Zmienne formularza z wartością początkową
        self.path_var = tk.StringVar()           # Ścieżka do analizowanego pliku/folderu
        self.out_var = tk.StringVar()            # Ścieżka do eksportu .txt
        self.xlsx_var = tk.StringVar()           # Ścieżka do eksportu .xlsx
        self.pdf_var = tk.StringVar()            # Ścieżka do eksportu .pdf
        self.html_var = tk.StringVar()           # Ścieżka do eksportu .html
        self.recursive_var = tk.BooleanVar(value=True)  # Czy rekurencja w folderach
        self.detailed_stats_var = tk.BooleanVar(value=False)         # Szczegółowe statystyki
        self.very_detailed_stats_var = tk.BooleanVar(value=False)    # Bardzo szczegółowe statystyki
        self.explain_metrics_var = tk.BooleanVar(value=True)         # Wyjaśnij metryki
        self.html_top_languages_var = tk.BooleanVar(value=False)     # Top 5 języków w HTML
        self.html_safe_mode_var = tk.BooleanVar(value=True)          # Tryb bezpieczny HTML (szybsze ładowanie)
        self.git_var = tk.BooleanVar()          # Czy włączyć analizę git
        self.git_start_var = tk.StringVar()     # Początek zakresu dla git
        self.git_end_var = tk.StringVar()       # Koniec zakresu dla git

        # Zmienna służąca do blokowania przycisku "Analizuj" w trakcie pracy
        self._running = False
        self._build_ui()
        self._bind_shortcuts()

    # ------------------------------------------------------------------
    # Budowanie UI (okna, menu, panele, przyciski itd.)
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Buduje główne okno aplikacji oraz dodaje wszystkie panele sterujące."""
        self._build_menu()

        # Główne okno dzielone na panel boczny (opcje) oraz panel wyników.
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(8, 0))

        left = tk.Frame(paned, padx=4, bg="#f3f4f6")
        paned.add(left, weight=0)
        right = tk.Frame(paned, bg="#f8fafc")
        paned.add(right, weight=2)

        self._build_controls(left)
        self._build_output(right)
        self._build_statusbar()

    def _build_menu(self) -> None:
        """Tworzy pasek menu (Plik, Pomoc)."""
        menubar = tk.Menu(self.root)

        # Menu "Plik"
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Otwórz plik…", command=self.pick_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Otwórz folder…", command=self.pick_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Wyczyść formularz", command=self.clear_form)
        file_menu.add_separator()
        file_menu.add_command(label="Zakończ", command=self.root.quit)
        menubar.add_cascade(label="Plik", menu=file_menu)

        # Menu "Pomoc"
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="O programie", command=self._show_about)
        menubar.add_cascade(label="Pomoc", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_controls(self, parent: tk.Frame) -> None:
        """Buduje panel boczny z kontrolkami formularza i opcjami."""
        # ── Plik źródłowy ────────────────────────────────────────────
        src_frame = ttk.LabelFrame(parent, text="Plik źródłowy", padding=(8, 4))
        src_frame.pack(fill=tk.X, pady=(0, 8))
        path_row = tk.Frame(src_frame)
        path_row.pack(fill=tk.X)
        # Pole tekstowe do wpisania ścieżki
        ent = tk.Entry(path_row, textvariable=self.path_var)
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ent.focus()
        # Przyciski do wyboru pliku/folderu
        tk.Button(path_row, text="Plik", command=self.pick_file, width=6).pack(side=tk.LEFT, padx=(5,2))
        tk.Button(path_row, text="Folder", command=self.pick_folder, width=6).pack(side=tk.LEFT)
        # Checkbox: analiza rekurencyjna
        tk.Checkbutton(
            src_frame, text="Analiza rekurencyjna (dla folderów)", variable=self.recursive_var
        ).pack(anchor="w", pady=(5, 0))

        # ── Eksport raportów ──────────────────────────────────────────
        exp_frame = ttk.LabelFrame(parent, text="Eksport raportów  (opcjonalne)", padding=(8, 4))
        exp_frame.pack(fill=tk.X, pady=(0, 8))
        # Wiersze dla eksportów .txt, .xlsx, .pdf, .html
        for label, var, cmd in (
            (".txt ", self.out_var, self.pick_output),
            (".xlsx", self.xlsx_var, self.pick_output_xlsx),
            (".pdf ", self.pdf_var, self.pick_output_pdf),
            (".html", self.html_var, self.pick_output_html),
        ):
            row = tk.Frame(exp_frame)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, width=5, anchor="w", font=("TkDefaultFont", 9, "bold")).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
            tk.Button(row, text="…", command=cmd, width=3).pack(side=tk.LEFT)

        # ── Opcje analizy ─────────────────────────────────────────────
        opt_frame = ttk.LabelFrame(parent, text="Opcje analizy", padding=(8, 4))
        opt_frame.pack(fill=tk.X, pady=(0, 8))
        self.cb_detailed = tk.Checkbutton(
            opt_frame,
            text="Szczegółowe statystyki (złożoność, duplikaty)",
            variable=self.detailed_stats_var,
            command=self._on_detailed_toggle,
        )
        self.cb_detailed.pack(anchor="w", pady=(2,0))
        # Checkbox na "bardzo szczegółowe statystyki"
        self.cb_very_detailed = tk.Checkbutton(
            opt_frame,
            text="Bardzo szczegółowe statystyki (wszystkie metryki)",
            variable=self.very_detailed_stats_var,
            state=tk.DISABLED,  # Odblokowywany po zaznaczeniu "szczegółowych"
        )
        self.cb_very_detailed.pack(anchor="w", padx=(22,0))
        # Pomocniczy tooltip dla bardzo szczegółowych statystyk
        _tip(self.cb_very_detailed, "Wymaga włączenia 'Szczegółowych statystyk' powyżej.")

        ttk.Separator(opt_frame, orient="horizontal").pack(fill=tk.X, pady=(7, 5))

        # Opcja dodania wyjaśnienia metryk w raporcie
        cb_explain = tk.Checkbutton(
            opt_frame, text="Wyjaśnij metryki (tryb nauki)", variable=self.explain_metrics_var
        )
        cb_explain.pack(anchor="w")
        _tip(cb_explain, "Dodaje sekcję z opisem każdej metryki w raporcie tekstowym.")

        ttk.Separator(opt_frame, orient="horizontal").pack(fill=tk.X, pady=(7, 4))

        # Sekcja opcji raportu HTML
        tk.Label(opt_frame, text="Opcje raportu HTML:", font=("TkDefaultFont", 9)).pack(anchor="w", pady=(0,2))

        cb_top = tk.Checkbutton(
            opt_frame,
            text='Top 5 języków (reszta jako "Inne")',
            variable=self.html_top_languages_var,
        )
        cb_top.pack(anchor="w", padx=(16, 0))

        cb_safe = tk.Checkbutton(
            opt_frame,
            text="Tryb wydajności HTML (bezpiecznik)",
            variable=self.html_safe_mode_var,
        )
        cb_safe.pack(anchor="w", padx=(16, 0), pady=(0,2))
        _tip(cb_safe, "Ogranicza liczbę wierszy w raporcie HTML dla szybszego ładowania strony.")

        # ── Git (opcjonalne) ──────────────────────────────────────────
        git_frame = ttk.LabelFrame(parent, text="Analiza Git  (opcjonalne)", padding=(8, 4))
        git_frame.pack(fill=tk.X, pady=(0, 7))
        # Checkbox włączający dodatkowe opcje analizy Gita
        tk.Checkbutton(
            git_frame, text="Włącz analizę Git", variable=self.git_var, command=self._on_git_toggle
        ).pack(anchor="w")
        # Podpanel ukrywający się gdy git_var == False
        self.git_options_frame = tk.Frame(git_frame)
        inner = tk.Frame(self.git_options_frame)
        inner.pack(fill=tk.X, pady=(5,0))
        # Pola do ustawienia zakresu commitów
        tk.Label(inner, text="Początek:").grid(row=0, column=0, sticky="w")
        tk.Entry(inner, textvariable=self.git_start_var, width=16).grid(row=0, column=1, padx=(4,11))
        tk.Label(inner, text="Koniec:").grid(row=0, column=2, sticky="w")
        tk.Entry(inner, textvariable=self.git_end_var, width=16).grid(row=0, column=3, padx=(4, 0))
        _tip(inner, "Format: 'YYYY-MM-DD' lub '1 month ago', 'now'")

        # ── Przyciski akcji + pasek postępu ──────────────────────────
        action_frame = tk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(4, 3))
        # Przycisk do rozpoczęcia analizy
        self.btn_analyze = tk.Button(
            action_frame,
            text="▶   Analizuj",
            command=self.run_analysis,
            bg="#2563eb",
            fg="white",
            activebackground="#1e429f",
            activeforeground="white",
            font=("TkDefaultFont", 14, "bold"),
            relief=tk.RAISED,
            bd=2,
            padx=22,
            pady=10,
            cursor="hand2",
            highlightbackground="#1a56db",
            highlightthickness=2,
        )
        self.btn_analyze.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Przycisk do czyszczenia wszystkich pól formularza
        tk.Button(
            action_frame,
            text="Wyczyść",
            command=self.clear_form,
            relief=tk.FLAT,
            padx=10,
            pady=6,
        ).pack(side=tk.LEFT, padx=(7, 0))

        # Pasek postępu informujący o stanie analizy
        self.progress = ttk.Progressbar(parent, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(5, 0))

    def _build_output(self, parent: tk.Frame) -> None:
        """Buduje panel wyświetlania wyników analizy."""
        tk.Label(
            parent, text="Wyniki analizy", font=("TkDefaultFont", 11, "bold"), anchor="w"
        ).pack(fill=tk.X, padx=8, pady=(6, 6))
        frame = tk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0,7))
        self.text = tk.Text(frame, wrap="word", font=("TkFixedFont", 11))
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _build_statusbar(self) -> None:
        """Dodaje dolny pasek statusu."""
        bar = tk.Frame(self.root, bd=1, relief=tk.SUNKEN)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_var = tk.StringVar(value="Gotowy")
        tk.Label(
            bar, textvariable=self.status_var, anchor="w", font=("TkDefaultFont", 9)
        ).pack(side=tk.LEFT, padx=8, pady=2)

    # ------------------------------------------------------------------
    # Skroty klawiaturowe (hotkeys)
    # ------------------------------------------------------------------

    def _bind_shortcuts(self) -> None:
        """Ustawia skróty klawiaturowe (Enter, Ctrl+O)."""
        self.root.bind("<Return>", lambda _e: self.run_analysis())
        self.root.bind("<Control-o>", lambda _e: self.pick_file())

    # ------------------------------------------------------------------
    # Pomocnicze przelaczniki (do dynamicznego włączania opcji)
    # ------------------------------------------------------------------

    def _on_detailed_toggle(self) -> None:
        """Odblokowuje 'bardzo szczegółowe statystyki' przy zaznaczeniu 'szczegółowych'."""
        if self.detailed_stats_var.get():
            self.cb_very_detailed.config(state=tk.NORMAL)
        else:
            self.very_detailed_stats_var.set(False)
            self.cb_very_detailed.config(state=tk.DISABLED)

    def _on_git_toggle(self) -> None:
        """Pokazuje/ukrywa dodatkowe opcje dla analizy Git."""
        if self.git_var.get():
            self.git_options_frame.pack(fill=tk.X, padx=(18, 0), pady=(6, 0))
        else:
            self.git_options_frame.pack_forget()

    # ------------------------------------------------------------------
    # Okna wyboru plikow (do obsługi przycisków Plik/Folder/Eksport)
    # ------------------------------------------------------------------

    def pick_file(self) -> None:
        """Dialog do wyboru pojedynczego pliku źródłowego."""
        path = filedialog.askopenfilename()
        if path:
            self.path_var.set(path)

    def pick_folder(self) -> None:
        """Dialog do wyboru folderu źródłowego."""
        path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)

    def pick_output(self) -> None:
        """Dialog do wyboru ścieżki eksportu .txt"""
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text file", "*.txt")])
        if path:
            self.out_var.set(path)

    def pick_output_xlsx(self) -> None:
        """Dialog do wyboru ścieżki eksportu .xlsx"""
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel file", "*.xlsx")])
        if path:
            self.xlsx_var.set(path)

    def pick_output_pdf(self) -> None:
        """Dialog do wyboru ścieżki eksportu .pdf"""
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF file", "*.pdf")])
        if path:
            self.pdf_var.set(path)

    def pick_output_html(self) -> None:
        """Dialog do wyboru ścieżki eksportu .html"""
        path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML file", "*.html")])
        if path:
            self.html_var.set(path)

    # ------------------------------------------------------------------
    # Czyszczenie formularza (zerowanie pól, czyszczenie wyników w oknie)
    # ------------------------------------------------------------------

    def clear_form(self) -> None:
        """Czyści wszystkie pola formularza oraz wyniki analizy."""
        for var in (self.path_var, self.out_var, self.xlsx_var, self.pdf_var,
                    self.html_var, self.git_start_var, self.git_end_var):
            var.set("")
        self.text.delete("1.0", tk.END)
        self._set_status("Formularz wyczyszczony.")

    # ------------------------------------------------------------------
    # Obsluga statusu i wyjscia (obsługa pasku statusu oraz wyniku)
    # ------------------------------------------------------------------

    def _set_status(self, msg: str) -> None:
        """Ustawia tekst w pasku statusu."""
        self.status_var.set(msg)

    def _append_output(self, message: str = "") -> None:
        """Dopisuje komunikat do wyjściowego tekstu wyników (panel po prawej)."""
        self.text.insert(tk.END, message + "\n")
        self.text.see(tk.END)

    # ------------------------------------------------------------------
    # Analiza w tle (UI pozostaje responsywne dzięki threading)
    # ------------------------------------------------------------------

    def run_analysis(self) -> None:
        """Inicjuje analizę - sprawdza ścieżkę, blokuje UI i uruchamia analizę w tle."""
        if self._running:
            return  # Zabezpieczenie: nie rozpoczynaj analizy jeśli już trwa

        path_text = self.path_var.get().strip()
        if not path_text:
            messagebox.showerror("Błąd", "Podaj ścieżkę do pliku lub folderu.")
            return

        path = Path(path_text).expanduser().resolve()
        if not path.exists():
            messagebox.showerror("Błąd", f"Ścieżka nie istnieje:\n{path}")
            return

        self._running = True
        self.btn_analyze.config(state=tk.DISABLED)
        self.progress.start(12)  # Rozpocznij animację paska postępu
        self._set_status("Analizuję…")
        self.text.delete("1.0", tk.END)
        threading.Thread(target=self._do_analysis, args=(path,), daemon=True).start()

    def _do_analysis(self, path: Path) -> None:
        """Wykonuje właściwą analizę w osobnym wątku (żeby UI nie zamrażało się)."""
        try:
            # Krok 0: zbierz pliki do analizy (od razu sprawdz czy coś jest)
            files = analyzer.collect_files(path, recursive=self.recursive_var.get())
            if not files:
                # Komunikat o braku plików do analizy
                self.root.after(
                    0,
                    lambda: messagebox.showerror("Błąd", "Brak obsługiwanych plików do analizy."),
                )
                return

            # Krok 1: Analityka każdego pliku po kolei
            results = [analyzer.analyze_file(fp) for fp in files]

            # Krok 2: Zbuduj raport tekstowy
            report = analyzer.build_report(
                path,
                results,
                include_detailed_stats=self.detailed_stats_var.get(),
                include_very_detailed_stats=self.very_detailed_stats_var.get(),
                explain_metrics=self.explain_metrics_var.get(),
            )

            # Krok 3: Zapis raportów (opcjonalnie) do różnych formatów
            saved_paths: list[Path] = []
            out_str = self.out_var.get().strip()
            if out_str:
                # Zapis tekstowego raportu
                out_path = Path(out_str).expanduser().resolve()
                out_path.write_text(report + "\n", encoding="utf-8")
                saved_paths.append(out_path)

            xlsx_str = self.xlsx_var.get().strip()
            if xlsx_str:
                # Zapis raportu Excel
                try:
                    xlsx_path = Path(xlsx_str).expanduser().resolve()
                    analyzer.write_xlsx_report(path, results, xlsx_path)
                    saved_paths.append(xlsx_path)
                except RuntimeError as exc:
                    self.root.after(0, lambda e=exc: messagebox.showerror("Błąd", str(e)))
                    return

            pdf_str = self.pdf_var.get().strip()
            if pdf_str:
                # Zapis PDF z wizualizacją
                try:
                    pdf_path = Path(pdf_str).expanduser().resolve()
                    analyzer.create_visualization_report(path, results, pdf_path)
                    saved_paths.append(pdf_path)
                except RuntimeError as exc:
                    self.root.after(0, lambda e=exc: messagebox.showerror("Błąd", str(e)))
                    return

            # Krok 4: analiza Git i wykres zmian (opcjonalne).
            git_commits: list[dict] = []
            if self.git_var.get():
                try:
                    git_commits = analyzer.analyze_git_changes(
                        path,
                        self.git_start_var.get().strip() or None,
                        self.git_end_var.get().strip() or None,
                    )
                    if git_commits:
                        # Jeśli znaleziono commity, wygeneruj wykres PNG i dodaj do listy eksportów
                        git_chart_path = path.parent / f"{path.name}_git_analysis.png"
                        analyzer.create_git_report(path, git_commits, git_chart_path)
                        saved_paths.append(git_chart_path)
                except RuntimeError as exc:
                    self.root.after(0, lambda e=exc: messagebox.showerror("Błąd analizy Git", str(e)))
                    return

            # Krok 5: zapis HTML (opcjonalny) z ograniczoną lub pełną wersją tabeli
            html_str = self.html_var.get().strip()
            if html_str:
                try:
                    html_path = Path(html_str).expanduser().resolve()
                    kwargs: dict = dict(top_languages_only=self.html_top_languages_var.get())
                    # Parametry ograniczające wielkość tabeli w HTML
                    if self.html_safe_mode_var.get():
                        kwargs |= dict(max_languages=12, max_quality_rows=300, max_file_rows=600)
                    else:
                        kwargs |= dict(max_languages=200, max_quality_rows=5000, max_file_rows=5000)
                    analyzer.create_html_report(path, results, html_path, **kwargs)
                    saved_paths.append(html_path)
                except RuntimeError as exc:
                    self.root.after(0, lambda e=exc: messagebox.showerror("Błąd", str(e)))
                    return

            # Po wszystkim, pokaż wyniki w GUI, odblokuj UI itp.
            self.root.after(
                0,
                lambda: self._show_results(path, report, saved_paths, git_commits, results),
            )

        except Exception as exc:
            # Obsługa każdego nieprzewidzianego błędu
            self.root.after(0, lambda e=exc: messagebox.showerror("Błąd", str(e)))
        finally:
            # Zawsze zwolnij blokadę przycisku/paska postępu
            self.root.after(0, self._analysis_done)

    def _show_results(
        self,
        path: Path,
        report: str,
        saved_paths: list[Path],
        git_commits: list[dict],
        results: list,
    ) -> None:
        """Wyświetla raport oraz podsumowanie zapisu plików i ew. GIT info."""
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, report)

        if saved_paths:
            # Komunikat o zapisanych plikach
            files_list = "\n".join(f"• {p}" for p in saved_paths)
            messagebox.showinfo("Zapisano pliki", f"Zapisano {len(saved_paths)} plik(ów):\n\n{files_list}")

        if git_commits:
            # Dodaj podsumowanie GIT pod wynikami
            self._append_output("")
            self._append_output("=== Analiza zmian Git ===")
            self._append_output(f"Znaleziono {len(git_commits)} commitów.")
            total_added = sum(c["lines_added"] for c in git_commits)
            total_removed = sum(c["lines_removed"] for c in git_commits)
            total_files = sum(c["files_changed"] for c in git_commits)
            self._append_output(
                f"Łączne zmiany: +{total_added} -{total_removed}"
                f" (netto: {total_added - total_removed})"
            )
            self._append_output(f"Łącznie zmienionych plików: {total_files}")

        self._set_status(f"Analiza zakończona  ·  {len(results)} plik(ów)  ·  {path.name}")

    def _analysis_done(self) -> None:
        """Odblokowuje przycisk oraz pasek postępu po zakończonej analizie."""
        self._running = False
        self.progress.stop()
        self.btn_analyze.config(state=tk.NORMAL)

    # ------------------------------------------------------------------
    # Pozostale / Drobne pomocnicze
    # ------------------------------------------------------------------

    def _show_about(self) -> None:
        """Wyświetla okienko 'O programie'."""
        messagebox.showinfo(
            "O programie",
            "Code Learning Analyzer v2\n\nNarzędzie do analizy kodu źródłowego.\nPomaga w nauce i ocenie jakości kodu.",
        )

def main() -> None:
    """Funkcja główna — uruchamia pętlę Tkintera."""
    root = tk.Tk()
    app = AnalyzerApp(root)
    _ = app  # Pozwala "przetrzymać" zmienną, żeby nie została zgubiona przez GC
    root.mainloop()

if __name__ == "__main__":
    main()
