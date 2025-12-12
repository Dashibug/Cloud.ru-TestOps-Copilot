from pathlib import Path
from typing import Optional

from jinja2 import Template

from cloudru_agent.models.requirements import UiRequirementsDocument
from cloudru_agent.llm.evolution_client import EvolutionClient

UI_PYTEST_TEMPLATE = Template(
    '''import allure
import pytest
from playwright.sync_api import Page, expect


CALC_URL = "{{ base_url }}"


@allure.feature("{{ feature }}")
@allure.story("{{ block_name }}")
@allure.title({{ title_literal }})
@allure.tag("{{ requirement.priority }}")
@allure.label("priority", "{{ requirement.priority }}")
@allure.label("requirement", "{{ requirement.id }}")
def test_ui_{{ requirement.id|lower }}(page: Page) -> None:
    with allure.step("Arrange: {{ arrange_text }}"):
        {{ arrange_code }}

    with allure.step("Act: {{ act_text }}"):
        {{ act_code }}

    with allure.step("Assert: {{ assert_text }}"):
        {{ assert_code }}
'''
)


class UiPytestGenerator:
    """
    Генерация UI-автотестов (pytest + Playwright) из UiRequirementsDocument.

    Если передан llm (EvolutionClient), то шаги Arrange/Act/Assert
    генерируются моделью + проверяются ревизором.
    """

    def __init__(self, base_url: str = "https://cloud.ru/calculator") -> None:
        self.base_url = base_url

    def generate(
        self,
        doc: UiRequirementsDocument,
        output_dir: str,
        llm: Optional[EvolutionClient] = None,
    ) -> None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        for req in doc.requirements:
            # Текстовые описания шагов (AAA)
            arrange_text = getattr(req, "arrange", None) or "открыть страницу продукта"
            act_text = getattr(req, "act", None) or "выполнить действия пользователя"
            assert_text = getattr(req, "assert_", None) or "проверить ожидаемый результат"

            # Дефолтный код, если LLM вдруг не сработает
            arrange_code = "page.goto(CALC_URL)"
            act_code = "pass  # FIXME: добавить шаги взаимодействия с UI"
            assert_code = "pass  # FIXME: добавить проверки"
            title_literal = repr(req.title or req.id)

            # === 1. Генератор: просим Evolution FM сгенерировать код Playwright ===
            if llm is not None:
                try:
                    steps = llm.ui_playwright_steps(doc.feature, req)
                    arrange_lines = steps.get("arrange") or []
                    act_lines = steps.get("act") or []
                    assert_lines = steps.get("assert") or []

                    if arrange_lines:
                        arrange_code = "\n        ".join(arrange_lines)
                    else:
                        arrange_code = "page.goto(CALC_URL)"

                    if act_lines:
                        act_code = "\n        ".join(act_lines)

                    if assert_lines:
                        assert_code = "\n        ".join(assert_lines)

                except Exception:
                    arrange_code = "page.goto(CALC_URL)"
                    act_code = "pass  # LLM error, требуется доработка шага"
                    assert_code = "pass  # LLM error, требуется доработка проверки"

            # Рендерим сам тест
            test_code = UI_PYTEST_TEMPLATE.render(
                base_url=self.base_url,
                feature=doc.feature,
                block_name=req.block,
                requirement=req,
                title_literal=title_literal,
                arrange_text=arrange_text,
                act_text=act_text,
                assert_text=assert_text,
                arrange_code=arrange_code,
                act_code=act_code,
                assert_code=assert_code,
            )

            # === 2. Ревизор: даём модели проверить сгенерированный тест ===
            if llm is not None:
                try:
                    review = llm.review_ui_test(req.title, test_code)
                    if not review.get("ok", True):
                        problems = review.get("problems") or []
                        comment = "# REVIEW WARNING: ревизор нашёл проблемы:\n"
                        for p in problems:
                            comment += f"# - {p}\n"
                        comment += "\n"
                        test_code = comment + test_code
                except Exception:
                    pass

            file_name = f"test_ui_{req.id.lower()}.py"
            (out / file_name).write_text(test_code, encoding="utf-8")
