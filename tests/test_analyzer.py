from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import analyzer


class AnalyzerTests(unittest.TestCase):
    def test_collect_files_filters_unsupported_single_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsupported = root / "notes.txt"
            unsupported.write_text("hello", encoding="utf-8")

            files = analyzer.collect_files(unsupported)
            self.assertEqual(files, [])

    def test_collect_files_recursive_finds_supported_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("print('x')\n", encoding="utf-8")
            sub = root / "sub"
            sub.mkdir()
            (sub / "b.js").write_text("function x() { return 1; }\n", encoding="utf-8")
            (sub / "c.txt").write_text("ignore me\n", encoding="utf-8")

            files = analyzer.collect_files(root, recursive=True)
            names = [item.name for item in files]
            self.assertEqual(names, ["a.py", "b.js"])

    def test_analyze_file_counts_core_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code_file = root / "sample.py"
            long_line = "x = '" + ("a" * 120) + "'\n"
            code_file.write_text(
                "# comment\n"
                "def hello():\n"
                "    pass\n"
                "\n"
                "todo = 'TODO: improve'\n"
                + long_line,
                encoding="utf-8",
            )

            stats = analyzer.analyze_file(code_file)
            self.assertEqual(stats.total_lines, 6)
            self.assertEqual(stats.empty_lines, 1)
            self.assertEqual(stats.comment_lines, 1)
            self.assertEqual(stats.function_count, 1)
            self.assertEqual(stats.todo_count, 1)
            self.assertGreaterEqual(stats.long_lines, 1)

    def test_analyze_file_handles_css_block_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            css_file = root / "style.css"
            css_file.write_text(
                "/* start\n"
                "middle\n"
                "end */\n"
                ".box { color: red; }\n",
                encoding="utf-8",
            )

            stats = analyzer.analyze_file(css_file)
            self.assertEqual(stats.comment_lines, 3)
            self.assertEqual(stats.code_lines, 1)

    def test_learning_tips_mentions_todo_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code_file = root / "tiny.py"
            code_file.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

            stats = analyzer.analyze_file(code_file)
            summary = analyzer.summarize([stats])
            tips = analyzer.learning_tips(summary, [stats])

            self.assertTrue(any("TODO" in tip for tip in tips))

    def test_build_report_can_include_metric_explanations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code_file = root / "tiny.py"
            code_file.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

            stats = analyzer.analyze_file(code_file)
            report = analyzer.build_report(root, [stats], explain_metrics=True)

            self.assertIn("=== Jak czytac metryki ===", report)

    def test_language_usage_stats_aggregates_by_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            py_file = root / "a.py"
            js_file = root / "b.js"
            py_file.write_text("def x():\n    return 1\n", encoding="utf-8")
            js_file.write_text("function y() { return 2; }\n", encoding="utf-8")

            results = [analyzer.analyze_file(py_file), analyzer.analyze_file(js_file)]
            usage = analyzer.language_usage_stats(results)
            languages = {item["language"] for item in usage}

            self.assertIn("Python", languages)
            self.assertIn("JavaScript", languages)


if __name__ == "__main__":
    unittest.main()
