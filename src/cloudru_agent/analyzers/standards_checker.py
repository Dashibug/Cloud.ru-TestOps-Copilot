from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from pydantic import BaseModel


class StandardsIssue(BaseModel):
    file: str
    message: str


class StandardsReport(BaseModel):
    root_dir: str
    issues: List[StandardsIssue]
    ok_files: List[str]


class StandardsChecker:
    """
    Очень простой чекер стандартов:
    - проверяет наличие AAA (Arrange / Act / Assert);
    - проверяет наличие @allure.title и приоритета.
    """

    def check_dir(self, root: Path) -> StandardsReport:
        root = root.resolve()
        issues: List[StandardsIssue] = []
        ok_files: List[str] = []

        for file in root.rglob("test_*.py"):
            if not file.is_file():
                continue

            text = file.read_text(encoding="utf-8")

            has_title = "@allure.title" in text
            has_priority = (
                    'label("priority"' in text
                    or "label('priority'" in text
                    or "@allure.tag(" in text
            )
            has_arrange = "Arrange:" in text
            has_act = "Act:" in text
            has_assert = "Assert:" in text

            missing = []
            if not has_title:
                missing.append("нет @allure.title")
            if not has_priority:
                missing.append("нет метки priority")
            if not (has_arrange and has_act and has_assert):
                missing.append("нет полного AAA (Arrange/Act/Assert)")

            if missing:
                issues.append(
                    StandardsIssue(
                        file=file.name,
                        message=", ".join(missing),
                    )
                )
            else:
                ok_files.append(file.name)

        return StandardsReport(
            root_dir=str(root),
            issues=issues,
            ok_files=ok_files,
        )
