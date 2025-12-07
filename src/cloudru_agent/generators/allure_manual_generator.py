from pathlib import Path
from jinja2 import Template
from typing import Optional

from cloudru_agent.models.requirements import UiRequirementsDocument, ApiRequirementsDocument
from cloudru_agent.llm.evolution_client import EvolutionClient

UI_MANUAL_TEMPLATE = Template(
    '''import allure
from pytest import mark


owner = "qa-team"
feature = "{{ feature }}"
story = "{{ block_name }}"
test_type = "UI"


@allure.manual
@allure.label("owner", owner)
@allure.feature(feature)
@allure.story(story)
@allure.suite(test_type)
@mark.manual
class {{ class_name }}:

    @allure.title("{{ requirement.title }}")
    @allure.tag("{{ requirement.priority }}")
    @allure.label("priority", "{{ requirement.priority }}")
    def test_{{ requirement.id|lower }}(self) -> None:
        with allure.step("Arrange: {{ arrange_step }}"):
            ...
        with allure.step("Act: {{ act_step }}"):
            ...
        with allure.step("Assert: {{ assert_step }}"):
            ...
'''
)


class AllureManualGenerator:
    """
    Генерирует Python-файлы с тест-кейсами в формате Allure TestOps as Code.
    """

    def generate_ui_tests(
            self,
            doc: UiRequirementsDocument,
            output_dir: str,
            llm: Optional[EvolutionClient] = None,
    ) -> None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        for req in doc.requirements:
            # генерим AAA через LLM (если он есть)
            if llm is not None:
                steps = llm.ui_aaa_for_requirement(req)
                arrange_step = steps["arrange"]
                act_step = steps["act"]
                assert_step = steps["assert"]
            else:
                arrange_step = "описать предусловия"
                act_step = "выполнить действия пользователя"
                assert_step = "проверить ожидаемый результат"

            class_name = f"{req.block.title().replace('_', '')}Tests"
            content = UI_MANUAL_TEMPLATE.render(
                feature=doc.feature,
                block_name=req.block,
                class_name=class_name,
                requirement=req,
                arrange_step=arrange_step,
                act_step=act_step,
                assert_step=assert_step,
            )
            file_path = out / f"test_{req.id.lower()}.py"
            file_path.write_text(content, encoding="utf-8")

    def generate_api_tests(self, doc: ApiRequirementsDocument, output_dir: str) -> None:
        # Аналогично, но с другим шаблоном под API
        ...
