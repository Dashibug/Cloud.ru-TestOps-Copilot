from pathlib import Path
from jinja2 import Template
from typing import Optional

from cloudru_agent.models.requirements import UiRequirementsDocument, ApiRequirementsDocument
from cloudru_agent.llm.evolution_client import EvolutionClient

# --- шаблон для UI ---
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

# --- шаблон для API ---
API_MANUAL_TEMPLATE = Template(
    '''import allure
from pytest import mark


owner = "qa-team"
feature = "{{ feature }}"
section = "{{ requirement.section }}"
test_type = "API"


@allure.manual
@allure.label("owner", owner)
@allure.feature(feature)
@allure.story(section)
@allure.suite(test_type)
@mark.manual
class {{ class_name }}:

    @allure.title("{{ requirement.summary }} ({{ requirement.method }} {{ requirement.path }})")
    @allure.tag("{{ requirement.priority }}")
    @allure.label("priority", "{{ requirement.priority }}")
    @allure.label("endpoint", "{{ requirement.method }} {{ requirement.path }}")
    @allure.label("requirement", "{{ requirement.id }}")
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
            # генерим AAA через LLM
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

    def generate_api_tests(self, doc: ApiRequirementsDocument, output_dir: str, llm: Optional[EvolutionClient] = None) -> None:
        """
        Генерирует ручные API-тест-кейсы (Allure TestOps as Code).
        Если передан llm — шаги Arrange/Act/Assert берём из Evolution FM.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        for req in doc.requirements:
            # дефолтные шаги, если LLM не сработает
            arrange_step = f"подготовить авторизованный запрос к {req.method} {req.path}"
            act_step = f"отправить запрос {req.method} {req.path}"
            assert_step = (
                f"получить HTTP {req.success_code} и проверить тело ответа по спецификации"
            )

            if llm is not None:
                try:
                    steps = llm.api_aaa_steps(req)
                    arrange_step = steps.get("arrange", arrange_step)
                    act_step = steps.get("act", act_step)
                    assert_step = steps.get("assert", assert_step)
                except Exception:
                    pass

            class_name = f"{req.section}ApiTests"
            content = API_MANUAL_TEMPLATE.render(
                feature=doc.feature,
                requirement=req,
                class_name=class_name,
                arrange_step=arrange_step,
                act_step=act_step,
                assert_step=assert_step,
            )

            file_path = out / f"test_{req.id.lower()}.py"
            file_path.write_text(content, encoding="utf-8")

