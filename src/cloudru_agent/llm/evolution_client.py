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
    - переменная окружения API_KEY
    - base_url: https://foundation-models.api.cloud.ru/v1
    """

    def __init__(
        self,
        gen_model: str | None = None,
        review_model: str | None = None,
    ) -> None:

        load_dotenv()

        base_url = "https://foundation-models.api.cloud.ru/v1"

        api_key = os.getenv("API_KEY")
        if not api_key:
            raise RuntimeError(
                "API key not found. Set EVOLUTION_API_KEY or API_KEY in environment variables/"
                ".env before running the agent."
            )

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

        # Модель для генерации (разбор требований, AAA, Playwright-код)
        self.gen_model = os.getenv(
            "EVOLUTION_GEN_MODEL"
        )
        # Модель для ревью сгенерированного кода
        self.review_model = os.getenv(
            "EVOLUTION_REVIEW_MODEL"
        )
    # --- базовый чат-запрос ---

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """
        Простая обёртка вокруг chat.completions.create.
        Возвращает содержимое message.content первой choice.
        Использует модель генерации по умолчанию.
        """
        response = self.client.chat.completions.create(
            model=self.gen_model,
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
            model=self.gen_model,
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
            model=self.gen_model,
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

    # --- AAA для API-требования ---

    def api_aaa_steps(self, requirement) -> dict:
        """
        Генерирует Arrange / Act / Assert для одного API-требования.
        requirement: ApiRequirement
        """
        system_prompt = """
        Ты опытный QA-инженер по API. 
        Тебе даётся информация об одном HTTP-эндпоинте Evolution Compute.
        Нужно придумать понятные пошаговые действия в паттерне AAA.

        Верни JSON вида:
        {
        "arrange": "что подготовить перед вызовом",
        "act": "что именно вызвать",
        "assert": "что проверить в ответе"
        }

        Пиши по-русски, в одном-двух предложениях на шаг.""".strip()

        user_prompt = f"""
        Секция: {requirement.section}
        Метод: {requirement.method}
        Путь: {requirement.path}
        Краткое описание: {requirement.summary}
        Успешный код ответа: {requirement.success_code}
        Коды ошибок: {requirement.error_codes}""".strip()

        response = self.client.chat.completions.create(
            model=self.gen_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},)

        raw = response.choices[0].message.content

        try:
            data = json.loads(raw)
        except Exception:
            # запасной вариант, если модель вернула невалидный JSON
            return {
                "arrange": f"подготовить авторизованный запрос к {requirement.method} {requirement.path}",
                "act": f"отправить запрос {requirement.method} {requirement.path}",
                "assert": f"убедиться, что код ответа {requirement.success_code} и тело соответствует спецификации",
            }

        arrange = data.get("arrange") or f"подготовить авторизованный запрос к {requirement.method} {requirement.path}"
        act = data.get("act") or f"отправить запрос {requirement.method} {requirement.path}"
        assert_ = data.get("assert") or f"убедиться, что код ответа {requirement.success_code} и тело соответствует спецификации"

        return {
            "arrange": arrange,
            "act": act,
            "assert": assert_,
        }

    def ui_playwright_steps(self, feature: str, requirement) -> dict:
        """
        Генерирует реальные шаги Playwright для UI-теста.
        Возвращает dict с ключами: arrange, act, assert — списки строк Python-кода.
        """
        system_prompt = """ Ты Senior QA automation engineer. 
        Твоя задача — сгенерировать минимальный, но рабочий фрагмент автотеста на Python + Playwright (sync API).

        Контекст:
        - В тесте уже импортировано: 
        from playwright.sync_api import Page, expect
        - В сигнатуре теста есть параметр page: Page.
        - В модуле объявлена константа CALC_URL — базовый URL продукта.
        - Allure-steps уже обёрнуты вокруг кода, поэтому их писать не нужно.

        Требования к ответу:
        - Верни JSON-объект с ключами "arrange", "act", "assert".
        - Каждое значение — список строк Python-кода (без отступов, без with, без объявления функции).
        - В блоке arrange ОБЯЗАТЕЛЬНО должен быть вызов page.goto(CALC_URL).
        - В act опиши действия пользователя (поиск элементов, клики, ввод текста и т.п.).
        - В assert добавь реальные проверки через expect или assert.
        - Не используй '...', 'pass' и комментарии TODO.
        - Используй text/role-селекторы Playwright (get_by_role, get_by_text и т.п.).
        """.strip()

        user_prompt = f""" 
        Фича/продукт: {feature}
        Блок/экран: {getattr(requirement, "block", "")}
        ID требования: {requirement.id}
        Текст требования: {requirement.title}
        Приоритет: {getattr(requirement, "priority", "")}

        Сгенерируй Python-код для этого требования.
        """.strip()

        response = self.client.chat.completions.create(
            model=self.gen_model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt},
                      ],
            )
        content = response.choices[0].message.content
        try:
            data = json.loads(content)
        except Exception:
            # если модель вернула что-то не JSON — вернем пустые шаги
            data = {"arrange": [], "act": [], "assert": []}
        return data

    # --- Ревью автотеста ---

    def review_ui_test(self, requirement_title: str, test_code: str) -> dict:
        """
        Ревизор: проверяет, покрывает ли тест требование.
        Возвращает JSON: {"ok": bool, "problems": [...]}.
        """
        system_prompt = """
        Ты выступаешь как ревизор автотестов (senior QA lead).
        Твоя задача — по требованию и коду теста на Python + Playwright оценить,
        насколько тест действительно проверяет это требование.

        Обрати внимание на:
        - есть ли переход на нужный экран (Arrange),
        - есть ли ключевые действия пользователя (Act),
        - есть ли проверки по сути требования (Assert),
        - не отсутствуют ли вообще проверки (expect/assert).

        Ответ верни строго в JSON-формате:
        {
        "ok": true/false,
        "problems": ["краткое описание проблемы", ...]
        }""".strip()

        user_prompt = f"""Требование:
        {requirement_title}
        Код теста:
        ```python
        {test_code}""".strip()

        response = self.client.chat.completions.create(
            model=self.review_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        try:
            data = json.loads(content)
        except Exception:
            data = {"ok": True, "problems": []}
        return data

    # Исправление авто тестов

    def refine_ui_test_with_feedback(
        self,
        feature: str,
        requirement: UiRequirement,
        old_code: str,
        review: dict,
    ) -> str:
        """
        Улучшает автотест на основе фидбэка ревизора.
        На вход: фича, требование, старый код, JSON-ответ ревизора.
        На выход: полностью переписанный тестовый код (Python + Playwright).
        """

        problems = review.get("problems") or []
        problems_text = "\n".join(f"- {p}" for p in problems) or "нет явных проблем, но сделай тест чуть лучше"

        system_prompt = """
        Ты Senior QA automation engineer.

        Тебе передают:
        - формулировку требования к UI (на русском),
        - старый автотест на Python + Playwright,
        - список проблем от ревьюера (QA lead).

        Твоя задача — ПЕРЕПИСАТЬ тест так, чтобы:
        - все замечания ревьюера были исправлены;
        - сохранялась структура Arrange / Act / Assert с контекстом allure.step;
        - использовались те же импорты и константа CALC_URL;
        - не было '...', 'pass', TODO и лишних комментариев.

        Важно:
        - Не пиши markdown, не оборачивай код в ```python.
        - Верни ТОЛЬКО готовый код теста на Python.
        """.strip()

        user_prompt = f"""
        Фича / продукт: {feature}
        Блок: {getattr(requirement, "block", "")}
        ID требования: {requirement.id}
        Название: {requirement.title}
        Описание: {requirement.description}

        Старый код теста:
        ```python
        {old_code}
        ```

        Проблемы от ревьюера:
        {problems_text}

        Перепиши тест с учётом всех замечаний.
        """.strip()

        response = self.client.chat.completions.create(
            model=self.gen_model,  # или review_model, если хочешь более умный фикс
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content or ""



