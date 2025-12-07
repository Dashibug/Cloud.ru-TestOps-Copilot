import json
import os
from typing import List, Dict, Any

from openai import OpenAI
from dotenv import load_dotenv
from cloudru_agent.models.requirements import UiRequirementsDocument, UiRequirement


class EvolutionClient:
    """
    Обёртка над Evolution Foundation Models (OpenAI-совместимый API).

    Требует:
    - переменная окружения API_KEY (или CLOUDRU_FM_API_KEY)
    - base_url: https://foundation-models.api.cloud.ru/v1
    """

    def __init__(
        self,
        model: str = "openai/gpt-oss-120b",
        base_url: str = "https://foundation-models.api.cloud.ru/v1",
        api_key_env: str = "API_KEY",
    ) -> None:

        load_dotenv()

        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise RuntimeError(
                f"API key not found in environment variable {api_key_env}. "
                f"Set it before running the agent."
            )

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = model

    # --- базовый чат-запрос ---

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """
        Простой обёрткой вокруг chat.completions.create.
        Возвращает содержимое message.content первой choice.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    # --- специализированный метод: текст требований -> JSON требований ---

    def ui_requirements_from_text(self, text: str) -> UiRequirementsDocument:
        """
        Просит LLM преобразовать свободный текст требований по калькулятору
        в JSON нужного нам формата, затем собирает UiRequirementsDocument.
        """

        system_prompt = (
            "Ты опытный QA-лид. Твоя задача — из текста требований по UI "
            "калькулятора цен Cloud.ru выделить атомарные требования и вернуть "
            "СТРОГО валидный JSON без комментариев в формате:\n"
            "{\n"
            '  \"feature\": \"Cloud.ru Price Calculator\",\n'
            '  \"requirements\": [\n'
            "    {\n"
            '      \"id\": \"REQ_SOME_ID\",           # SNAKE_CASE, латиница, коротко\n'
            '      \"block\": \"BLOCK_1_START_PAGE\", # один из блоков: BLOCK_1_START_PAGE, BLOCK_2_CATALOG,\n'
            '      \"title\": \"Краткое название требования\", \n'
            '      \"description\": \"Расширенное описание\", \n'
            '      \"priority\": \"CRITICAL\" | \"NORMAL\" | \"LOW\"\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Не добавляй ничего, кроме JSON. Не используй комментарии или лишний текст."
        )

        user_prompt = (
            "Вот текст требований по UI-калькулятору Cloud.ru. "
            "Разбей его на отдельные требования:\n\n"
            f"{text}"
        )

        # просим модель вернуть json_object
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        raw_content = response.choices[0].message.content
        data = json.loads(raw_content)
        return UiRequirementsDocument(**data)

    def ui_aaa_for_requirement(self, requirement: UiRequirement) -> dict:
        """
        Генерирует текст шагов Arrange/Act/Assert для UI-требования.
        Возвращает словарь: {"arrange": "...", "act": "...", "assert": "..."}.
        """
        system_prompt = (
            "Ты опытный QA-инженер. Для каждого требования по UI калькулятору "
            "составляй понятные шаги в паттерне Arrange-Act-Assert. "
            "Отвечай СТРОГО JSON без комментариев вида:\n"
            "{\n"
            '  "arrange": "...",\n'
            '  "act": "...",\n'
            '  "assert": "..."\n'
            "}\n"
            "Шаги должны быть короткими, на русском, в повелительном наклонении."
        )

        user_prompt = (
            f"Требование ID: {requirement.id}\n"
            f"Блок: {requirement.block}\n"
            f"Название: {requirement.title}\n"
            f"Описание: {requirement.description}\n"
            f"Приоритет: {requirement.priority}\n"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content or "{}")
        return {
            "arrange": data.get("arrange", "открыть страницу калькулятора"),
            "act": data.get("act", requirement.title),
            "assert": data.get("assert", f"проверить: {requirement.title}"),
        }