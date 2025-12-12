from pathlib import Path
import json

from cloudru_agent.llm.evolution_client import EvolutionClient
from cloudru_agent.parsers.ui_requirements_parser import UiRequirementsParser
from cloudru_agent.parsers.openapi_parser import OpenApiParser
from cloudru_agent.generators.allure_manual_generator import AllureManualGenerator
from cloudru_agent.generators.ui_pytest_generator import UiPytestGenerator
from cloudru_agent.generators.api_pytest_generator import ApiPytestGenerator
from cloudru_agent.analyzers.coverage_analyzer import CoverageAnalyzer
from cloudru_agent.analyzers.standards_checker import StandardsChecker


class AgentOrchestrator:
    """
    Главный координатор: решает, какие модули вызывать и в каком порядке.
    Поддерживает любой UI-продукт через ui_base_url и ui_feature_name.
    """

    def __init__(
        self,
        ui_base_url: str = "https://cloud.ru/calculator",
        ui_feature_name: str = "UI продукта",
    ) -> None:
        # общие компоненты
        self.ui_parser = UiRequirementsParser()
        self.openapi_parser = OpenApiParser()
        self.manual_generator = AllureManualGenerator()
        self.api_auto_generator = ApiPytestGenerator()
        self.coverage_analyzer = CoverageAnalyzer()
        self.standards_checker = StandardsChecker()
        self.llm = EvolutionClient()

        # параметры UI-продукта
        self.ui_base_url = ui_base_url
        self.ui_feature_name = ui_feature_name

        # генератор UI-автотестов знает BASE_URL
        self.ui_auto_generator = UiPytestGenerator(base_url=ui_base_url)

    # =====================================================================
    # UI
    # =====================================================================

    def generate_ui_from_text(self, text: str, output_dir: str) -> None:
        """
        Кейс 1: текст требований -> Evolution FM -> требования -> ручные кейсы + автотесты.

        Парсер получает feature, чтобы:
        - подставить его в модель вместо «Cloud.ru Price Calculator»;
        - сохранить в UiRequirementsDocument.feature (для генераторов и ревизора).
        """
        requirements_doc = self.ui_parser.parse_text_with_llm(
            text,
            self.llm,
            feature=self.ui_feature_name,
        )

        manual_dir = Path(output_dir) / "manual_ui"
        auto_dir = Path(output_dir) / "auto_ui"

        manual_dir.mkdir(parents=True, exist_ok=True)
        auto_dir.mkdir(parents=True, exist_ok=True)

        # 1) Генерация ручных кейсов
        self.manual_generator.generate_ui_tests(
            requirements_doc,
            str(manual_dir),
            llm=self.llm,
        )

        # 2) Генерация первых версий автотестов (pytest + Playwright)
        self.ui_auto_generator.generate(
            requirements_doc,
            str(auto_dir),
            llm=self.llm,
        )

        # 3) Проход ревизора + авто-фиксер поверх сгенерированных автотестов
        self._review_and_refine_ui_autotests(requirements_doc, auto_dir)

    def _review_and_refine_ui_autotests(self, requirements_doc, auto_dir: Path) -> None:
        """
        Прогоняет сгенерированные UI-автотесты через ревизора и авто-фиксер.

        Ожидается, что UiPytestGenerator создаёт файлы в формате:
        test_ui_<req.id.lower()>.py

        Пример:
            req.id = "REQ_MAIN_PAGE_DISPLAY"
            -> файл: test_ui_req_main_page_display.py
        """
        for req in requirements_doc.requirements:
            file_name = f"test_ui_{req.id.lower()}.py"
            test_path = auto_dir / file_name

            if not test_path.exists():
                continue

            raw_code = test_path.read_text(encoding="utf-8")

            has_fixme = "FIXME" in raw_code or "pass  # FIXME" in raw_code

            if has_fixme:
                # если есть заглушки - считаем тест заведомо плохим, не спрашивая ревизора
                review = {
                    "ok": False,
                    "problems": [
                        "В тесте остались заглушки FIXME / pass — автогенерация не смогла построить шаги Act/Assert, тест неполный."
                    ],
                }
            else:
                # обычный путь: спрашиваем ревизора-модель
                try:
                    review = self.llm.review_ui_test(req.title, raw_code)
                except Exception:
                    # если что-то упало — пропускаем авто-фикс, но тест уже без фиксми
                    continue

            if review.get("ok", True):
                # ревизор (или наша проверка) считает тест нормальным
                continue

            # авто-фикс поверх проблемного теста
            try:
                improved_code = self.llm.refine_ui_test_with_feedback(
                    feature=requirements_doc.feature,
                    requirement=req,
                    old_code=raw_code,
                    review=review,
                )
            except Exception:
                continue

            if not improved_code or not improved_code.strip():
                continue

            problems = review.get("problems") or []
            if problems:
                problems_comment = "\n".join(f"# - {p}" for p in problems)
                header = (
                    "# REVIEW AUTO-FIX: тест автоматически переписан по замечаниям ревизора\n"
                    "# Найденные проблемы:\n"
                    f"{problems_comment}\n\n"
                )
            else:
                header = "# REVIEW AUTO-FIX: тест автоматически улучшен ревизором\n\n"

            final_code = header + improved_code.lstrip()
            test_path.write_text(final_code, encoding="utf-8")

    def generate_ui_manual_tests(self, requirements_path: str, output_dir: str) -> None:
        doc = self.ui_parser.parse(Path(requirements_path))
        self.manual_generator.generate_ui_tests(doc, output_dir, llm=self.llm)

    def generate_ui_automation(self, requirements_path: str, output_dir: str) -> None:
        doc = self.ui_parser.parse(Path(requirements_path))
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        self.ui_auto_generator.generate(doc, str(out_dir), llm=self.llm)
        self._review_and_refine_ui_autotests(doc, out_dir)

    # =====================================================================
    # API (OpenAPI v3)
    # =====================================================================

    def generate_api_manual_tests(self, openapi_path: str, output_dir: str) -> None:
        """
        CLI / утилита: ручные API-кейсы из OpenAPI-файла.
        """
        doc = self.openapi_parser.parse_file(openapi_path)
        self.manual_generator.generate_api_tests(doc, output_dir, llm=self.llm)

    def generate_api_automation(self, openapi_path: str, output_dir: str) -> None:
        """
        CLI / утилита: pytest API-тесты из OpenAPI-файла.
        """
        doc = self.openapi_parser.parse_file(openapi_path)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        self.api_auto_generator.generate_api_tests(doc, str(out_dir), llm=self.llm)
        self._review_and_refine_api_autotests(doc, out_dir)

    def generate_api_from_openapi_text(
        self,
        openapi_text: str,
        output_dir: str = "generated/api_from_openapi",
    ) -> None:
        """
        Кейс 2 (для Streamlit): разобрать OpenAPI 3.0 и
        сгенерировать ручные кейсы + pytest API-тесты.
        """
        doc = self.openapi_parser.parse_text(openapi_text)

        manual_dir = Path(output_dir) / "manual_api"
        auto_dir = Path(output_dir) / "auto_api"

        manual_dir.mkdir(parents=True, exist_ok=True)
        auto_dir.mkdir(parents=True, exist_ok=True)

        self.manual_generator.generate_api_tests(doc, str(manual_dir), llm=self.llm)
        self.api_auto_generator.generate_api_tests(doc, str(auto_dir), llm=self.llm)

        # ревью + авто-фикс для API
        self._review_and_refine_api_autotests(doc, auto_dir)

    def generate_api_from_openapi_file(
        self,
        openapi_path: str,
        output_dir: str = "generated/api_from_openapi",
    ) -> None:
        """
        Альтернатива: взять спецификацию из файла (yaml/json).
        """
        doc = self.openapi_parser.parse_file(openapi_path)

        manual_dir = Path(output_dir) / "manual_api"
        auto_dir = Path(output_dir) / "auto_api"

        manual_dir.mkdir(parents=True, exist_ok=True)
        auto_dir.mkdir(parents=True, exist_ok=True)

        self.manual_generator.generate_api_tests(doc, str(manual_dir), llm=self.llm)
        self.api_auto_generator.generate_api_tests(doc, str(auto_dir), llm=self.llm)

        # ревью + авто-фикс для API
        self._review_and_refine_api_autotests(doc, auto_dir)

    def _review_and_refine_api_autotests(self, requirements_doc, auto_dir: Path) -> None:
        """
        Прогоняет сгенерированные API-автотесты через ревизора и авто-фиксер.

        Файлы генерируются ApiPytestGenerator в формате:
            test_<req.id.lower()>.py
        """
        for req in requirements_doc.requirements:
            file_name = f"test_{req.id.lower()}.py"
            test_path = auto_dir / file_name

            if not test_path.exists():
                continue

            raw_code = test_path.read_text(encoding="utf-8")

            has_todo = "TODO" in raw_code or "pass" in raw_code

            if has_todo:
                review = {
                    "ok": False,
                    "problems": [
                        "В тесте остались заглушки TODO / pass — автогенерация не дописала шаги или проверки, тест неполный."
                    ],
                }
            else:
                try:
                    review = self.llm.review_api_test(req, raw_code)
                except Exception:
                    continue

            if review.get("ok", True):
                continue

            try:
                improved_code = self.llm.refine_api_test_with_feedback(
                    requirement=req,
                    old_code=raw_code,
                    review=review,
                    base_url=requirements_doc.base_url,
                )
            except Exception:
                continue

            if not improved_code or not improved_code.strip():
                continue

            problems = review.get("problems") or []
            if problems:
                problems_comment = "\n".join(f"# - {p}" for p in problems)
                header = (
                    "# REVIEW AUTO-FIX: API-тест автоматически переписан по замечаниям ревизора\n"
                    "# Найденные проблемы:\n"
                    f"{problems_comment}\n\n"
                )
            else:
                header = "# REVIEW AUTO-FIX: API-тест автоматически улучшен ревизором\n\n"

            final_code = header + improved_code.lstrip()
            test_path.write_text(final_code, encoding="utf-8")

    # =====================================================================
    # Аналитика
    # =====================================================================

    def analyze_tests(self, tests_dir: str) -> None:
        tests_path = Path(tests_dir)
        coverage_report = self.coverage_analyzer.analyze_dir(tests_path)
        standards_report = self.standards_checker.check_dir(tests_path)

        print("=== COVERAGE ===")
        print(json.dumps(coverage_report.model_dump(), ensure_ascii=False, indent=2))
        print("=== STANDARDS ===")
        print(json.dumps(standards_report.model_dump(), ensure_ascii=False, indent=2))
