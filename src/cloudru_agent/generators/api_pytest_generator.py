from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Template

from cloudru_agent.models.requirements import ApiRequirementsDocument


API_PYTEST_TEMPLATE = Template(
    '''import allure
import pytest
import requests


BASE_URL = "{{ base_url }}"


@allure.feature("{{ feature }}")
@allure.story("{{ requirement.section }}")
@allure.tag("{{ requirement.priority }}")
@allure.label("requirement", "{{ requirement.id }}")
@allure.label("endpoint", "{{ requirement.method }} {{ requirement.path }}")
def test_{{ requirement.id|lower }}(userPlaneApiToken: str) -> None:
    """
    {{ requirement.summary }}
    """
    with allure.step("Arrange: {{ arrange_step }}"):
        url = BASE_URL + "{{ requirement.path }}"
        headers = {"Authorization": f"Bearer {userPlaneApiToken}"}
        # TODO: собрать тело/параметры запроса при необходимости

    with allure.step("Act: {{ act_step }}"):
        response = requests.{{ requirement.method|lower }}(
            url,
            headers=headers,
            # json=payload,
        )

    with allure.step("Assert: {{ assert_step }}"):
        assert response.status_code == {{ requirement.success_code }}
        # TODO: добавить проверки структуры тела ответа и полей
'''
)


class ApiPytestGenerator:
    """
    Генерирует pytest-тесты для API на основе ApiRequirementsDocument.
    """

    def generate_api_tests(
        self,
        doc: ApiRequirementsDocument,
        output_dir: str,
        llm: Any | None = None,
    ) -> None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        for req in doc.requirements:
            arrange_step = (
                f"подготовить url, заголовки и (при необходимости) тело запроса для "
                f"{req.method} {req.path}"
            )
            act_step = f"отправить запрос {req.method} {req.path}"
            assert_step = (
                f"убедиться, что код ответа {req.success_code} и тело соответствует схеме"
            )

            if llm is not None:
                try:
                    steps = llm.api_aaa_steps(req)
                    arrange_step = steps.get("arrange", arrange_step)
                    act_step = steps.get("act", act_step)
                    assert_step = steps.get("assert", assert_step)
                except Exception:
                    pass

            content = API_PYTEST_TEMPLATE.render(
                base_url=doc.base_url,
                feature=doc.feature,
                requirement=req,
                arrange_step=arrange_step,
                act_step=act_step,
                assert_step=assert_step,
            )

            file_path = out / f"test_{req.id.lower()}.py"
            file_path.write_text(content, encoding="utf-8")
