from pathlib import Path
from jinja2 import Template
from typing import Optional
from cloudru_agent.llm.evolution_client import EvolutionClient
from cloudru_agent.models.requirements import UiRequirementsDocument

# Очень простой шаблон pytest + allure + Playwright
UI_PYTEST_TEMPLATE = Template(
    '''import allure
import pytest
from playwright.sync_api import Page


CALC_URL = "{{ base_url }}"


@allure.feature("{{ feature }}")
@allure.story("{{ block_name }}")
@allure.tag("{{ requirement.priority }}")
@allure.label("requirement", "{{ requirement.id }}")
def test_{{ requirement.id|lower }}(page: Page) -> None:
    with allure.step("Arrange: {{ arrange_step }}"):
        page.goto(CALC_URL)

    with allure.step("Act: {{ act_step }}"):
        # TODO: добавить реальные шаги взаимодействия с UI
        ...

    with allure.step("Assert: {{ assert_step }}"):
        # TODO: добавить реальные проверки
        ...
'''
)


class UiPytestGenerator:
    """
    Генерирует e2e UI автотесты (pytest) на основе UiRequirementsDocument.
    Пока без реальных шагов — заглушка для MVP.
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
            if llm is not None:
                steps = llm.ui_aaa_for_requirement(req)
                arrange_step = steps["arrange"]
                act_step = steps["act"]
                assert_step = steps["assert"]
            else:
                arrange_step = "открыть калькулятор"
                act_step = req.title
                assert_step = req.title

            block_name = req.block.replace("_", " ").title()
            content = UI_PYTEST_TEMPLATE.render(
                base_url=self.base_url,
                feature=doc.feature,
                block_name=block_name,
                requirement=req,
                arrange_step=arrange_step,
                act_step=act_step,
                assert_step=assert_step,
            )
            file_path = out / f"test_ui_{req.id.lower()}.py"
            file_path.write_text(content, encoding="utf-8")
