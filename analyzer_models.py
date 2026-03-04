"""Shared models and constants for Code Learning Analyzer."""

from __future__ import annotations

from dataclasses import dataclass


# [EN] Dictionary mapping file extensions to their comment prefixes
# [EN] This allows the analyzer to recognize comments in different programming languages
COMMENT_PREFIXES = {
    ".py": ["#"],                    # [EN] Python uses # for single-line comments
    ".js": ["//"],                   # [EN] JavaScript uses // for single-line comments
    ".ts": ["//"],                   # [EN] TypeScript uses // for single-line comments
    ".java": ["//"],                 # [EN] Java uses // for single-line comments
    ".c": ["//"],                    # [EN] C uses // for single-line comments
    ".cpp": ["//"],                  # [EN] C++ uses // for single-line comments
    ".cs": ["//"],                   # [EN] C# uses // for single-line comments
    ".go": ["//"],                   # [EN] Go uses // for single-line comments
    ".rs": ["//"],                   # [EN] Rust uses // for single-line comments
    ".php": ["//", "#"],             # [EN] PHP supports both // and # for comments
    ".sh": ["#"],                    # [EN] Shell scripts use # for comments
    ".html": ["<!--"],               # [EN] HTML uses <!-- --> for comments
    ".css": ["/*"],                  # [EN] CSS uses /* */ for comments
}

# [EN] Set of supported file extensions for analysis
SUPPORTED_EXTENSIONS = set(COMMENT_PREFIXES.keys())

LONG_LINE_LIMIT = 100

LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".sh": "Shell",
    ".html": "HTML",
    ".css": "CSS",
}


# [EN] Data class to store statistics for a single file
@dataclass
class FileStats:
    file: str
    total_lines: int
    empty_lines: int
    comment_lines: int
    code_lines: int
    long_lines: int
    todo_count: int
    function_count: int
    long_lines_details: list[tuple[int, str]]
    todo_details: list[tuple[int, str]]
    function_details: list[tuple[int, str]]


@dataclass
class AdvancedStats:
    """Advanced code quality and complexity statistics for a single file."""
    cyclomatic_complexity: int
    code_density: float
    duplication_score: float
    import_count: int
    class_count: int
    loop_count: int
    if_count: int
    try_catch_count: int


@dataclass
class SummaryStats:
    files_count: int
    total_lines: int
    empty_lines: int
    comment_lines: int
    code_lines: int
    long_lines: int
    todo_count: int
    function_count: int
