from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import re
from playwright.sync_api import sync_playwright, Page, Locator


# === модели отчёта ===
@dataclass
class LocatorIssue:
    """Проблема с конкретным локатором в файле автотеста."""

    file: str          # имя файла теста
    selector: str      # строка с выражением локатора, например page.get_by_role(...)
    message: str       # что не так (не нашёл элемент / упал eval и т.п.)


@dataclass
class UiLocatorsReport:
    """Результат проверки всех автотестов в директории."""

    ok_files: List[str]
    issues: List[LocatorIssue]

# === основной класс ===

class UiLocatorsChecker:
    """
    Проверяет, что локаторы из сгенерированных UI-автотестов
    реально находятся на странице по CALC_URL.

    Подход:
    - открываем страницу в Playwright один раз;
    - для каждого файла test_ui_*.py вытаскиваем выражения вида
      page.get_by_role(...), page.get_by_text(...), page.locator(...);
    - выполняем их через eval(page=...), проверяем, что count() > 0;
    - если не нашли или произошла ошибка — пишем LocatorIssue.
    """

    LOCATOR_PATTERNS = [
        re.compile(r"page\.get_by_role\([^)]*\)"),
        re.compile(r"page\.get_by_text\([^)]*\)"),
        re.compile(r"page\.get_by_label\([^)]*\)"),
        re.compile(r"page\.locator\([^)]*\)"),
        re.compile(r"page\.locator\((\"[^\"]*\"|'[^']*')\)"),
    ]

    def __init__(self, base_url: str, timeout_ms: int = 60_000) -> None:
        self.base_url = base_url
        self.timeout_ms = timeout_ms

    def analyze_dir(self, tests_dir: Path | str) -> UiLocatorsReport:
        tests_path = Path(tests_dir)
        ok_files: List[str] = []
        issues: List[LocatorIssue] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # грузим один раз
            page.goto(self.base_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            page.wait_for_timeout(1000)

            for file in sorted(tests_path.glob("test_ui_*.py")):
                file_issues = self._check_file(page, file)
                if file_issues:
                    issues.extend(file_issues)
                else:
                    ok_files.append(file.name)

            browser.close()

        return UiLocatorsReport(ok_files=ok_files, issues=issues)

    def _check_file(self, page: Page, file_path: Path) -> List[LocatorIssue]:
        source = file_path.read_text(encoding="utf-8")
        exprs = self._extract_locator_expressions(source)
        file_issues: List[LocatorIssue] = []

        for expr in exprs:
            try:
                # выполняем локатор на реальной странице
                locator: Locator = eval(expr, {"page": page})  # noqa: S307
                count = locator.count()
                if count == 0:
                    file_issues.append(
                        LocatorIssue(
                            file=file_path.name,
                            selector=expr,
                            message="Локатор не нашёл ни одного элемента на странице",
                        )
                    )
            except Exception as e:
                file_issues.append(
                    LocatorIssue(
                        file=file_path.name,
                        selector=expr,
                        message=f"Ошибка при проверке локатора: {e}",
                    )
                )

        return file_issues

    def _extract_locator_expressions(self, source: str) -> List[str]:
        """
        Извлекает из текста теста все выражения локаторов page.get_by_*/locator(...).

        Мы берём только сам кусок "page.get_by_role(...)" без обёрток expect(...).
        """
        exprs: List[str] = []
        for line in source.splitlines():
            for pattern in self.LOCATOR_PATTERNS:
                for match in pattern.finditer(line):
                    expr = match.group(0).strip()
                    if expr not in exprs:
                        exprs.append(expr)
        return exprs
