from pathlib import Path
from typing import List

from cloudru_agent.models.coverage import CoverageReport, CoverageEntry


class CoverageAnalyzer:
    """
    Очень простой анализ покрытия:
    считает количество тестовых файлов в директории и делит их на UI/API по имени файла.
    """

    def build_report(self, tests_dir: Path) -> CoverageReport:
        tests_dir = tests_dir.resolve()
        py_files: List[Path] = list(tests_dir.rglob("test_*.py"))

        ui_files = [p for p in py_files if "ui" in p.name]
        api_files = [p for p in py_files if "api" in p.name]

        entries = [
            CoverageEntry(
                scope="UI",
                total_tests=len(ui_files),
                files=[str(p.relative_to(tests_dir)) for p in ui_files],
            ),
            CoverageEntry(
                scope="API",
                total_tests=len(api_files),
                files=[str(p.relative_to(tests_dir)) for p in api_files],
            ),
        ]

        return CoverageReport(root_dir=str(tests_dir), entries=entries)
