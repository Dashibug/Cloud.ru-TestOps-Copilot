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
    Главный координатор: решает, какие агенты вызывать и в каком порядке.
    """

    def __init__(self) -> None:
        self.ui_parser = UiRequirementsParser()
        self.openapi_parser = OpenApiParser()
        self.manual_generator = AllureManualGenerator()
        self.ui_auto_generator = UiPytestGenerator()
        self.api_auto_generator = ApiPytestGenerator()
        self.coverage_analyzer = CoverageAnalyzer()
        self.standards_checker = StandardsChecker()
        self.llm = EvolutionClient()

    # =====================================================================
    # UI
    # =====================================================================

    def generate_ui_from_text(self, text: str, output_dir: str) -> None:
        """
        Кейс 1: текст требований -> Evolution FM -> требования -> ручные кейсы + автотесты.
        """
        requirements_doc = self.ui_parser.parse_text_with_llm(text, self.llm)

        manual_dir = Path(output_dir) / "manual_ui"
        auto_dir = Path(output_dir) / "auto_ui"

        self.manual_generator.generate_ui_tests(
            requirements_doc,
            str(manual_dir),
            llm=self.llm,
        )
        self.ui_auto_generator.generate(
            requirements_doc,
            str(auto_dir),
            llm=self.llm,
        )

    def generate_ui_manual_tests(self, requirements_path: str, output_dir: str) -> None:
        doc = self.ui_parser.parse(Path(requirements_path))
        self.manual_generator.generate_ui_tests(doc, output_dir, llm=self.llm)

    def generate_ui_automation(self, requirements_path: str, output_dir: str) -> None:
        doc = self.ui_parser.parse(Path(requirements_path))
        self.ui_auto_generator.generate(doc, output_dir, llm=self.llm)

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
        self.api_auto_generator.generate_api_tests(doc, output_dir, llm=self.llm)

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

        self.manual_generator.generate_api_tests(doc, str(manual_dir), llm=self.llm)
        self.api_auto_generator.generate_api_tests(doc, str(auto_dir), llm=self.llm)

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

        self.manual_generator.generate_api_tests(doc, str(manual_dir), llm=self.llm)
        self.api_auto_generator.generate_api_tests(doc, str(auto_dir), llm=self.llm)

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
