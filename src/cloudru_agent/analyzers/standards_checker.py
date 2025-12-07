from pathlib import Path
from typing import List
from pydantic import BaseModel


class StandardsIssue(BaseModel):
    file: str
    message: str
    severity: str  # "ERROR" | "WARNING"


class StandardsReport(BaseModel):
    root_dir: str
    issues: List[StandardsIssue]
    ok_files: List[str]


class StandardsChecker:
    """
    Простейший линтер:
    - проверяет наличие шагов Arrange/Act/Assert
    - проверяет наличие @allure.title
    """

    def check_dir(self, tests_dir: Path) -> StandardsReport:
        tests_dir = tests_dir.resolve()
        issues: List[StandardsIssue] = []
        ok_files: List[str] = []

        for file in tests_dir.rglob("test_*.py"):
            text = file.read_text(encoding="utf-8")
            file_rel = str(file.relative_to(tests_dir))

            missing = []
            if "with allure.step(\"Arrange" not in text and "with allure.step('Arrange" not in text:
                missing.append("Arrange")
            if "with allure.step(\"Act" not in text and "with allure.step('Act" not in text:
                missing.append("Act")
            if "with allure.step(\"Assert" not in text and "with allure.step('Assert" not in text:
                missing.append("Assert")
            if "@allure.title" not in text:
                missing.append("@allure.title")

            if missing:
                issues.append(
                    StandardsIssue(
                        file=file_rel,
                        message=f"Missing AAA parts / decorators: {', '.join(missing)}",
                        severity="WARNING",
                    )
                )
            else:
                ok_files.append(file_rel)

        return StandardsReport(root_dir=str(tests_dir), issues=issues, ok_files=ok_files)
