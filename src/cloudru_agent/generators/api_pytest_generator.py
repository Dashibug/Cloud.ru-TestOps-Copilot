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

@allure.title("{{ requirement.summary }}")
@allure.label("priority", "{{ requirement.priority }}")
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
        {{ arrange_code }}

    with allure.step("Act: {{ act_step }}"):
        {{ act_code }}

    with allure.step("Assert: {{ assert_step }}"):
        {{ assert_code }}
'''
)


class ApiPytestGenerator:
    """
    Генерирует pytest-тесты для API на основе ApiRequirementsDocument.

    Если передан llm, то:
    - текст шагов Arrange/Act/Assert берётся из LLM (api_aaa_steps),
    - реальный Python-код шагов берётся из LLM (api_requests_code).
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
            # --- Текстовые шаги (AAA) для подписи allure.step ---
            arrange_step = (
                f"подготовить url, заголовки и (при необходимости) тело запроса для "
                f"{req.method} {req.path}"
            )
            act_step = f"отправить запрос {req.method} {req.path}"
            assert_step = (
                f"убедиться, что код ответа {req.success_code} и тело соответствует схеме"
            )

            # --- Дефолтный код, если LLM не сработает ---
            arrange_code_lines = [
                f'url = BASE_URL + "{req.path}"',
                'headers = {"Authorization": f"Bearer {userPlaneApiToken}"}',
            ]
            act_code_lines = [
                f"response = requests.{req.method.lower()}(",
                "    url,",
                "    headers=headers,",
                ")",
            ]
            assert_code_lines = [
                f"assert response.status_code == {req.success_code}",
            ]

            if llm is not None:
                # 1) текстовые шаги AAA
                try:
                    steps = llm.api_aaa_steps(req)
                    arrange_step = steps.get("arrange", arrange_step)
                    act_step = steps.get("act", act_step)
                    assert_step = steps.get("assert", assert_step)
                except Exception:
                    pass

                # 2) реальный Python-код для requests
                try:
                    code_steps = llm.api_requests_code(doc.feature, req)
                    arr = code_steps.get("arrange")
                    act = code_steps.get("act")
                    ass = code_steps.get("assert")

                    if arr:
                        arrange_code_lines = arr
                    if act:
                        act_code_lines = act
                    if ass:
                        assert_code_lines = ass
                except Exception:
                    pass

            arrange_code = "\n        ".join(arrange_code_lines)
            act_code = "\n        ".join(act_code_lines)
            assert_code = "\n        ".join(assert_code_lines)

            content = API_PYTEST_TEMPLATE.render(
                base_url=doc.base_url,
                feature=doc.feature,
                requirement=req,
                arrange_step=arrange_step,
                act_step=act_step,
                assert_step=assert_step,
                arrange_code=arrange_code,
                act_code=act_code,
                assert_code=assert_code,
            )

            file_path = out / f"test_{req.id.lower()}.py"
            file_path.write_text(content, encoding="utf-8")
