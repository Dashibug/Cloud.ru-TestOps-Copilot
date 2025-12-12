from __future__ import annotations

import ast
from pathlib import Path
from typing import List

from pydantic import BaseModel


class CoverageEntry(BaseModel):
    scope: str  # UI или API
    total_tests: int
    files: List[str]


class CoverageReport(BaseModel):
    root_dir: str
    entries: List[CoverageEntry]


class CoverageAnalyzer:
    """
    Простейший анализ покрытия:
    - считает количество test_* функций в .py файлах;
    - собирает список файлов с тестами;
    - scope определяет по имени директории (ui / api).
    """

    def analyze_dir(self, root: Path) -> CoverageReport:
        root = root.resolve()

        scope = "API" if "api" in root.as_posix().lower() else "UI"
        total_tests = 0
        files_with_tests: List[str] = []

        for file in root.rglob("test_*.py"):
            if not file.is_file():
                continue

            try:
                code = file.read_text(encoding="utf-8")
                tree = ast.parse(code)
            except Exception:
                # если файл битый - пропускаем
                continue

            tests_in_file = sum(
                isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
                for node in ast.walk(tree)
            )

            if tests_in_file > 0:
                total_tests += tests_in_file
                files_with_tests.append(file.name)

        entry = CoverageEntry(scope=scope, total_tests=total_tests, files=files_with_tests)
        return CoverageReport(root_dir=str(root), entries=[entry])
