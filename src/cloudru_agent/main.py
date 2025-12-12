import typer
from dotenv import load_dotenv
from pathlib import Path
from cloudru_agent.orchestrator.orchestrator import AgentOrchestrator

app = typer.Typer(help="Cloud.ru Hack: test generation agent")
load_dotenv()

@app.command()
def generate_ui_manual(requirements_path: str, output_dir: str = "generated/manual_ui"):
    """
    Сгенерировать ручные тест-кейсы (Allure TestOps as Code)
    для UI из текстового файла с требованиями.
    """
    orchestrator = AgentOrchestrator()
    orchestrator.generate_ui_manual_tests(requirements_path, output_dir)


@app.command()
def generate_api_manual(openapi_path: str, output_dir: str = "generated/manual_api"):
    """
    Сгенерировать ручные тест-кейсы по OpenAPI (VMs, Disks, Flavors).
    """
    orchestrator = AgentOrchestrator()
    orchestrator.generate_api_manual_tests(openapi_path, output_dir)


@app.command()
def generate_ui_auto(requirements_path: str, output_dir: str = "generated/auto_ui"):
    """
    Сгенерировать e2e UI автотесты (pytest) на основе требований.
    """
    orchestrator = AgentOrchestrator()
    orchestrator.generate_ui_automation(requirements_path, output_dir)


@app.command()
def generate_api_auto(openapi_path: str, output_dir: str = "generated/auto_api"):
    """
    Сгенерировать API автотесты (pytest) на основе OpenAPI.
    """
    orchestrator = AgentOrchestrator()
    orchestrator.generate_api_automation(openapi_path, output_dir)


@app.command()
def analyze_tests(tests_dir: str):
    """
    Анализ покрытия и стандартов для уже сгенерированных тестов.
    """
    orchestrator = AgentOrchestrator()
    orchestrator.analyze_tests(tests_dir)

@app.command()
def generate_ui_from_text(
    text_path: str,
    output_dir: str = "generated/from_text",
):
    """
    Прочитать текст требований из файла и через Evolution FM
    сгенерировать ручные тест-кейсы + автотесты.
    """
    orchestrator = AgentOrchestrator()
    text = Path(text_path).read_text(encoding="utf-8")
    orchestrator.generate_ui_from_text(text, output_dir)


if __name__ == "__main__":
    app()
