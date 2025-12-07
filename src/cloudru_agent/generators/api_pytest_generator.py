from pathlib import Path
from jinja2 import Template

from cloudru_agent.models.requirements import ApiRequirementsDocument, ApiOperationRequirement

API_PYTEST_TEMPLATE = Template(
    '''import allure
import requests


BASE_URL = "{{ base_url }}"


@allure.feature("{{ service }}")
@allure.story("{{ requirement.resource }}")
@allure.label("requirement", "{{ requirement.id }}")
@allure.tag("{{ requirement.priority }}")
def test_{{ requirement.id|lower }}(auth_headers) -> None:
    url = BASE_URL + "{{ requirement.path }}"
    with allure.step("Arrange: подготовить данные запроса"):
        payload = {}  # TODO: заполнить по спецификации

    with allure.step("Act: выполнить {{ requirement.method }} {{ requirement.path }}"):
        response = requests.{{ requirement.method.lower() }}(
            url,
            json=payload if "{{ requirement.method }}" in ["POST", "PUT", "PATCH"] else None,
            headers=auth_headers,
        )

    with allure.step("Assert: базовые проверки ответа"):
        assert response.status_code < 500
        # TODO: добавить проверки схемы / кода статуса
'''
)


class ApiPytestGenerator:
    """
    Генерирует API автотесты (pytest + requests) на основе ApiRequirementsDocument.
    Пока с минимальными проверками.
    """

    def __init__(self, base_url: str = "https://compute.api.cloud.ru") -> None:
        self.base_url = base_url

    def generate(self, doc: ApiRequirementsDocument, output_dir: str) -> None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        for req in doc.operations:  # type: ApiOperationRequirement
            content = API_PYTEST_TEMPLATE.render(
                base_url=self.base_url,
                service=doc.service,
                requirement=req,
            )
            file_path = out / f"test_api_{req.id.lower()}.py"
            file_path.write_text(content, encoding="utf-8")
