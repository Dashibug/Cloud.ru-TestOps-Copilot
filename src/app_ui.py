import sys
from pathlib import Path
import shutil

import streamlit as st

# --- пути к проекту и примерам ---
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from cloudru_agent.orchestrator.orchestrator import AgentOrchestrator  # noqa: E402
from cloudru_agent.analyzers.coverage_analyzer import CoverageAnalyzer  # noqa: E402
from cloudru_agent.analyzers.standards_checker import StandardsChecker  # noqa: E402
from cloudru_agent.analyzers.ui_locators_checker import UiLocatorsChecker  # noqa: E402

EXAMPLES_DIR = SRC_DIR / "examples"
DEFAULT_UI_REQ_FILE = EXAMPLES_DIR / "ui_calc_requirements_text.md"

# куда кладём результаты генерации
GENERATED_UI_DIR = SRC_DIR / "generated" / "from_text"
GENERATED_API_DIR = SRC_DIR / "generated" / "api_from_openapi"


def load_default_ui_requirements() -> str:
    if DEFAULT_UI_REQ_FILE.exists():
        return DEFAULT_UI_REQ_FILE.read_text(encoding="utf-8")
    return (
        "Блок 1. Начальная страница\n\n"
        "- Опишите здесь требования к основному пользовательскому сценарию "
        "Cloud.ru Price Calculator..."
    )


def inject_cloudru_css() -> None:
    st.markdown(
        """
        <style>
        /* убираем стандартный верхний хедер Streamlit */
        header[data-testid="stHeader"] {
            background: transparent;
            box-shadow: none;
            height: 10;
            min-height: 0;
            padding: 0;
        }

        /* прячем статус и кнопку Stop */
        div[data-testid="stStatusWidget"] {
            display: none !important;
        }
        /* прячем кнопку Deploy (старое и новое имя класса) */
        .stDeployButton,
        .stAppDeployButton {
            display: none !important;
        }

        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }

        :root {
            --cloud-bg: #F3F6FB;
            --cloud-surface: #FFFFFF;
            --cloud-surface-soft: #F9FAFB;
            --cloud-border-subtle: #E2E8F0;
            --cloud-border-strong: #CBD5E1;
            --cloud-brand: #00A060;
            --cloud-brand-strong: #009256;
            --cloud-brand-soft: #E6F6EF;
            --cloud-text-main: #051723;
            --cloud-text-muted: #6B7280;
            --cloud-radius-lg: 16px;
            --cloud-radius-xl: 24px;
        }

        .stApp {
            background:
                radial-gradient(circle at 0 0, rgba(16,185,129,0.12), transparent 55%),
                radial-gradient(circle at 100% 0, rgba(59,130,246,0.09), transparent 55%),
                var(--cloud-bg);
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text",
                         "Segoe UI", system-ui, sans-serif;
            color: var(--cloud-text-main);
        }

        .block-container {
            max-width: 1200px;
            padding-top: 1.3rem;
            padding-bottom: 3rem;
        }

        /* шапка */
        .cloud-header {
            position: relative;
            padding: 1rem 1.3rem 1.1rem;
            margin-bottom: 1.4rem;
            border-radius: var(--cloud-radius-xl);
            background: linear-gradient(135deg, #FFFFFF 0%, #F3F6FB 100%);
            border: 1px solid rgba(148, 163, 184, 0.35);
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.5rem;
        }

        .cloud-header-left {
            display: flex;
            align-items: center;
            gap: 0.9rem;
        }

        .cloud-logo-circle {
            width: 40px;
            height: 40px;
            border-radius: 999px;
            background: radial-gradient(circle at 25% 0, #FFFFFF 0%, #00B368 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            box-shadow: 0 12px 30px rgba(5, 150, 105, 0.45);
        }

        .cloud-brand-block {
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
        }

        .cloud-badge {
            align-self: flex-start;
            padding: 0.1rem 0.65rem;
            border-radius: 999px;
            font-size: 0.7rem;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            background: var(--cloud-brand-soft);
            color: var(--cloud-brand);
            font-weight: 600;
        }

        .cloud-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--cloud-text-main);
        }

        .cloud-subtitle {
            font-size: 0.9rem;
            color: var(--cloud-text-muted);
        }

        .cloud-header-right {
            font-size: 0.82rem;
            color: var(--cloud-text-muted);
            text-align: right;
        }

        .cloud-header-right strong {
            color: var(--cloud-brand);
        }

        /* вкладки */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.6rem;
            padding-bottom: 0.35rem;
            border-bottom: 1px solid var(--cloud-border-subtle);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: 0.35rem 1.2rem;
            font-size: 0.93rem;
            color: var(--cloud-text-muted);
            background: transparent;
            border: 1px solid transparent;
            box-shadow: none;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(255, 255, 255, 0.7);
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: #FFFFFF;
            color: var(--cloud-brand);
            font-weight: 600;
            border-color: rgba(34, 197, 94, 0.55);
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.18);
        }

        .cloud-card {
            background: var(--cloud-surface);
            border-radius: var(--cloud-radius-lg);
            padding: 1.15rem 1.25rem 1.25rem;
            border: 1px solid rgba(148, 163, 184, 0.32);
            box-shadow: 0 16px 30px rgba(15, 23, 42, 0.07);
        }

        /* --- карточки сводки по проекту --- */
        .cloud-summary-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            margin: 0.8rem 0 1.4rem;
        }

        @media (max-width: 1000px) {
            .cloud-summary-grid {
                grid-template-columns: 1fr;
            }
        }

        .cloud-summary-card {
            background: var(--cloud-surface);
            border-radius: var(--cloud-radius-lg);
            padding: 1rem 1.2rem 1.1rem;
            border: 1px solid var(--cloud-border-subtle);
            box-shadow: 0 12px 26px rgba(15, 23, 42, 0.06);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 120px;
        }

        .cloud-summary-title {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--cloud-text-muted);
            margin-bottom: 0.35rem;
        }

        .cloud-summary-main {
            display: flex;
            align-items: baseline;
            gap: 0.35rem;
            margin-bottom: 0.35rem;
        }

        .cloud-summary-main-value {
            font-size: 1.6rem;
            font-weight: 700;
        }

        .cloud-summary-main-total {
            font-size: 0.9rem;
            color: var(--cloud-text-muted);
        }

        .cloud-summary-footer {
            font-size: 0.8rem;
            color: var(--cloud-text-muted);
        }

        .cloud-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.1rem 0.55rem;
            border-radius: 999px;
            background: var(--cloud-surface-soft);
            border: 1px solid var(--cloud-border-subtle);
            font-size: 0.78rem;
        }

        /* --- сетка и карточки для деталей UI/API --- */
        .cloud-details-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1rem;
            margin: 0.7rem 0 1.3rem;
        }

        @media (max-width: 1000px) {
            .cloud-details-grid {
                grid-template-columns: 1fr;
            }
        }

        .cloud-section-card {
            padding: 1rem 1.2rem 1.2rem;
        }

        .cloud-kpi-row {
            display: flex;
            align-items: baseline;
            gap: 0.35rem;
            margin: 0.35rem 0 0.15rem;
        }

        .cloud-kpi-value {
            font-size: 1.5rem;
            font-weight: 700;
        }

        .cloud-kpi-label {
            font-size: 0.9rem;
            color: var(--cloud-text-muted);
        }

        .cloud-kpi-footer {
            font-size: 0.85rem;
            color: var(--cloud-text-muted);
        }

        .cloud-details {
            margin-top: 0.6rem;
            padding: 0.5rem 0.7rem;
            border-radius: 0.7rem;
            background: var(--cloud-surface-soft);
            border: 1px dashed var(--cloud-border-subtle);
            font-size: 0.86rem;
        }

        .cloud-details summary {
            list-style: none;
            cursor: pointer;
            font-weight: 600;
        }

        .cloud-details summary::-webkit-details-marker {
            display: none;
        }

        .cloud-details ul {
            margin: 0.4rem 0 0;
            padding-left: 1.1rem;
        }

        .cloud-card h3, .cloud-card h2, .cloud-card h4 {
            margin-top: 0.1rem;
            margin-bottom: 0.6rem;
            font-weight: 600;
            color: var(--cloud-text-main);
        }

        .cloud-card .small-description {
            font-size: 0.85rem;
            color: var(--cloud-text-muted);
            margin-bottom: 0.75rem;
        }

        [data-testid="stFileUploaderDropzone"] {
            border-radius: 0.9rem;
            background: var(--cloud-surface-soft);
            border: 1px dashed var(--cloud-border-strong);
        }

        [data-testid="stFileUploaderDropzone"] > div {
            color: var(--cloud-text-muted);
        }

        textarea, .stTextInput>div>div>input {
            border-radius: 0.9rem !important;
            border: 1px solid var(--cloud-border-subtle);
            background: var(--cloud-surface-soft);
        }

        textarea:focus-visible,
        .stTextInput>div>div>input:focus-visible {
            outline: 2px solid rgba(34, 197, 94, 0.65) !important;
            outline-offset: 1px;
        }

        .stButton>button {
            border-radius: 999px;
            border: none;
            background: linear-gradient(120deg, #00B368, #22C55E);
            color: #FFFFFF;
            font-weight: 600;
            font-size: 0.92rem;
            padding: 0.42rem 1.45rem;
            box-shadow: 0 12px 22px rgba(16, 185, 129, 0.45);
            transition: transform 80ms ease-out, box-shadow 80ms ease-out, filter 80ms ease-out;
        }
        .stButton>button:hover {
            filter: brightness(1.04);
            transform: translateY(-0.5px);
            box-shadow: 0 14px 30px rgba(16, 185, 129, 0.55);
        }

        [data-testid="stAlert"] {
            border-radius: 0.9rem;
            border: 1px solid #BFDBFE;
            background: #EFF6FF;
        }

        pre, code {
            border-radius: 0.7rem !important;
        }

        .st-expander {
            border-radius: 0.8rem;
            border: 1px solid var(--cloud-border-subtle);
            background: var(--cloud-surface-soft);
        }

        [data-testid="stMetricValue"] {
            font-weight: 700;
        }
        [data-testid="stMetricLabel"] {
            color: var(--cloud-text-muted);
        }

        .block-container h2,
        .block-container h3 {
            font-size: 1.35rem !important;
            line-height: 1.25;
            margin-top: 0.2rem;
            margin-bottom: 0.9rem;
        }

        .stTabs [data-baseweb="tab-highlight"] {
            background-color: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Cloud.ru TestOps Copilot",
        layout="wide",
    )

    if "ui_generated" not in st.session_state:
        st.session_state["ui_generated"] = False
    if "api_generated" not in st.session_state:
        st.session_state["api_generated"] = False

    inject_cloudru_css()

    # --- шапка ---
    st.markdown(
        """
        <div class="cloud-header">
          <div class="cloud-header-left">
            <div class="cloud-logo-circle">☁️</div>
            <div class="cloud-brand-block">
              <div class="cloud-badge">Cloud.ru</div>
              <div class="cloud-title">TestOps Copilot</div>
              <div class="cloud-subtitle">
                ИИ-ассистент для генерации тест-кейсов и автотестов на базе Evolution Foundation Model
              </div>
            </div>
          </div>
          <div class="cloud-header-right">
            <div>Ускоряет подготовку UI и API-тестов</div>
            <div><strong>Меньше рутины</strong> для QA-команд</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- верхний уровень: вкладки ---
    ui_tab, api_tab, analytics_tab = st.tabs(
        ["UI-требования", "API-спецификация", "Аналитика"]
    )

    # =====================================================================
    # ТАБ 1. UI требования
    # =====================================================================
    with ui_tab:
        with st.sidebar:
            st.markdown("### Настройки продукта")

            if "show_settings" not in st.session_state:
                st.session_state["show_settings"] = True

            if st.session_state["show_settings"]:
                ui_base_url = st.text_input(
                    "BASE_URL тестируемого UI",
                    value=st.session_state.get("ui_base_url", "https://cloud.ru/calculator"),
                )

                ui_feature_name = st.text_input(
                    "Название продукта / фичи",
                    value=st.session_state.get("ui_feature_name", "Cloud.ru Price Calculator"),
                )

                st.session_state["ui_base_url"] = ui_base_url
                st.session_state["ui_feature_name"] = ui_feature_name

            st.markdown("---")

        # основной layout: слева требования, справа артефакты
        left, right = st.columns([1, 1])

        # левая колонка — требования
        with left:
            st.subheader("Описание пользовательского сценария")

            uploaded = st.file_uploader(
                "Загрузите файл с требованиями (md / txt) или введите текст ниже",
                type=["md", "txt"],
            )

            if uploaded is not None:
                ui_text = uploaded.read().decode("utf-8")
            else:
                ui_text = st.text_area(
                    "Текст UI-требований",
                    value=load_default_ui_requirements(),
                    height=400,
                )

            col_btn_gen, col_btn_clear = st.columns([1, 1])
            with col_btn_gen:
                generate_ui_button = st.button("Сгенерировать UI-тесты", type="primary")
            with col_btn_clear:
                clear_ui_button = st.button("Очистить UI-результаты")

            if clear_ui_button:
                shutil.rmtree(GENERATED_UI_DIR, ignore_errors=True)
                st.session_state["ui_generated"] = False
                st.success("Сгенерированные файлы удалены.")

        # правая колонка — артефакты
        with right:
            st.subheader("Сгенерированные артефакты для UI")

            if generate_ui_button:
                if not ui_text.strip():
                    st.error("Введите требования или загрузите файл.")
                else:
                    with st.spinner("Генерируем тест-кейсы и автотесты для UI..."):
                        orchestrator = AgentOrchestrator(
                            ui_base_url=ui_base_url,
                            ui_feature_name=ui_feature_name,
                        )
                        orchestrator.generate_ui_from_text(
                            ui_text,
                            str(GENERATED_UI_DIR),
                        )
                    st.session_state["ui_generated"] = True
                    st.success("Готово! UI-тесты сгенерированы.")

            manual_dir = GENERATED_UI_DIR / "manual_ui"
            auto_dir = GENERATED_UI_DIR / "auto_ui"

            if st.session_state["ui_generated"] and (
                    manual_dir.exists() or auto_dir.exists()
            ):
                tab_manual, tab_auto = st.tabs(
                    ["Ручные тест-кейсы (Allure)", "Автотесты (pytest + Playwright)"]
                )

                with tab_manual:
                    if not manual_dir.exists():
                        st.info("Ручные тесты ещё не сгенерированы.")
                    else:
                        for file in sorted(manual_dir.glob("*.py")):
                            with st.expander(f"📄 {file.name}"):
                                st.code(
                                    file.read_text(encoding="utf-8"),
                                    language="python",
                                )

                with tab_auto:
                    if not auto_dir.exists():
                        st.info("Автотесты ещё не сгенерированы.")
                    else:
                        for file in sorted(auto_dir.glob("*.py")):
                            with st.expander(f"🤖 {file.name}"):
                                st.code(
                                    file.read_text(encoding="utf-8"),
                                    language="python",
                                )
            else:
                st.info(
                    "Пока ничего не сгенерировано. Введите требования слева и нажмите "
                    "кнопку «Сгенерировать UI-тесты»."
                )

    # =====================================================================
    # ТАБ 2. API Evolution Compute
    # =====================================================================
    with api_tab:
        left, right = st.columns([1, 1])

        with left:
            st.subheader("OpenAPI-спецификация")

            openapi_file = st.file_uploader(
                "Загрузите OpenAPI спецификацию (yaml/json)",
                type=["yaml", "yml", "json", "txt"],
                key="openapi_uploader",
            )
            openapi_text_area = st.text_area(
                "Или вставьте сюда содержимое файла OpenAPI",
                height=300,
                key="openapi_text",
            )

            openapi_text = ""
            if openapi_file is not None:
                openapi_text = openapi_file.read().decode("utf-8")
            elif openapi_text_area.strip():
                openapi_text = openapi_text_area

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                generate_api_button = st.button("Сгенерировать API-тесты")
            with col_btn2:
                clear_api_button = st.button("Очистить API-результаты")

            if generate_api_button:
                if not openapi_text.strip():
                    st.error("Загрузите файл OpenAPI или вставьте текст спецификации.")
                else:
                    with st.spinner(
                            "Разбираем OpenAPI и генерируем API-тесты (manual + pytest)..."
                    ):
                        orchestrator = AgentOrchestrator()
                        orchestrator.generate_api_from_openapi_text(
                            openapi_text,
                            str(GENERATED_API_DIR),
                        )
                    st.session_state["api_generated"] = True
                    st.success("Готово! API-тесты сгенерированы.")

            if clear_api_button:
                shutil.rmtree(GENERATED_API_DIR, ignore_errors=True)
                st.session_state["api_generated"] = False
                st.success("Результаты по API очищены.")

        with right:
            st.subheader("Сгенерированные артефакты для API")

            manual_api_dir = GENERATED_API_DIR / "manual_api"
            auto_api_dir = GENERATED_API_DIR / "auto_api"

            if manual_api_dir.exists() or auto_api_dir.exists():
                tab_manual_api, tab_auto_api = st.tabs(
                    ["Ручные тест-кейсы (Allure)", "Pytest-тесты для API"]
                )

                with tab_manual_api:
                    if not manual_api_dir.exists():
                        st.info("Ручные API-кейсы ещё не сгенерированы.")
                    else:
                        for file in sorted(manual_api_dir.glob("*.py")):
                            with st.expander(f"📄 {file.name}"):
                                st.code(
                                    file.read_text(encoding="utf-8"),
                                    language="python",
                                )

                with tab_auto_api:
                    if not auto_api_dir.exists():
                        st.info("API-автотесты ещё не сгенерированы.")
                    else:
                        for file in sorted(auto_api_dir.glob("*.py")):
                            with st.expander(f"⚙️ {file.name}"):
                                st.code(
                                    file.read_text(encoding="utf-8"),
                                    language="python",
                                )
            else:
                st.info(
                    "Пока ничего не сгенерировано. Загрузите OpenAPI-спеку слева и "
                    "нажмите «Сгенерировать API-тесты»."
                )

    # =====================================================================
    # ТАБ 3. Аналитика
    # =====================================================================
    with analytics_tab:
        st.subheader("Аналитика покрытия и стандартов")

        manual_ui_dir = GENERATED_UI_DIR / "manual_ui"
        auto_ui_dir = GENERATED_UI_DIR / "auto_ui"
        manual_api_dir = GENERATED_API_DIR / "manual_api"
        auto_api_dir = GENERATED_API_DIR / "auto_api"

        has_any = any(
            d.exists() for d in (manual_ui_dir, auto_ui_dir, manual_api_dir, auto_api_dir)
        )

        # --- UI: локаторы Playwright ---
        ui_base_url = st.session_state.get(
            "ui_base_url",
            "https://cloud.ru/calculator",
        )
        ui_loc_ok = ui_loc_bad_files = ui_loc_total_files = 0
        ui_loc_status_text = "UI-автотесты ещё не сгенерированы."

        if auto_ui_dir.exists():
            checker = UiLocatorsChecker(base_url=ui_base_url)
            loc_report = checker.analyze_dir(auto_ui_dir)
            ui_loc_ok = len(loc_report.ok_files)
            ui_loc_bad_files = len({i.file for i in loc_report.issues})
            ui_loc_total_files = ui_loc_ok + ui_loc_bad_files

            if ui_loc_total_files == 0:
                ui_loc_status_text = "Не найдено файлов с локаторами."
            elif ui_loc_bad_files == 0:
                ui_loc_status_text = "✅ Все локаторы нашли элементы на странице."
            else:
                ui_loc_status_text = (
                    f"⚠️ Есть {ui_loc_bad_files} файлов с проблемными локаторами."
                )

        # --- Покрытие / проверка стандартов по файлам ---
        coverage_analyzer = CoverageAnalyzer()
        standards_checker = StandardsChecker()

        # UI manual
        ui_manual_total = ui_manual_ok = ui_manual_bad = 0
        ui_manual_issues = []
        if manual_ui_dir.exists():
            cov_manual = coverage_analyzer.analyze_dir(manual_ui_dir)
            std_manual = standards_checker.check_dir(manual_ui_dir)
            ui_manual_total = sum(e.total_tests for e in cov_manual.entries)
            ui_manual_ok = len(std_manual.ok_files)
            ui_manual_bad = len(std_manual.issues)
            ui_manual_issues = std_manual.issues

        # UI auto
        ui_auto_total = ui_auto_ok = ui_auto_bad = 0
        ui_auto_issues = []
        if auto_ui_dir.exists():
            cov_auto = coverage_analyzer.analyze_dir(auto_ui_dir)
            std_auto = standards_checker.check_dir(auto_ui_dir)
            ui_auto_total = sum(e.total_tests for e in cov_auto.entries)
            ui_auto_ok = len(std_auto.ok_files)
            ui_auto_bad = len(std_auto.issues)
            ui_auto_issues = std_auto.issues

        # API manual
        api_manual_total = api_manual_ok = api_manual_bad = 0
        api_manual_issues = []
        if manual_api_dir.exists():
            cov_api_manual = coverage_analyzer.analyze_dir(manual_api_dir)
            std_api_manual = standards_checker.check_dir(manual_api_dir)
            api_manual_total = sum(e.total_tests for e in cov_api_manual.entries)
            api_manual_ok = len(std_api_manual.ok_files)
            api_manual_bad = len(std_api_manual.issues)
            api_manual_issues = std_api_manual.issues

        # API auto
        api_auto_total = api_auto_ok = api_auto_bad = 0
        api_auto_issues = []
        if auto_api_dir.exists():
            cov_api_auto = coverage_analyzer.analyze_dir(auto_api_dir)
            std_api_auto = standards_checker.check_dir(auto_api_dir)
            api_auto_total = sum(e.total_tests for e in cov_api_auto.entries)
            api_auto_ok = len(std_api_auto.ok_files)
            api_auto_bad = len(std_api_auto.issues)
            api_auto_issues = std_api_auto.issues

        # --- Сводка по проекту ---
        st.markdown("### Сводка по проекту")

        total_ui_tests = ui_manual_total + ui_auto_total
        total_ui_bad_files = ui_manual_bad + ui_auto_bad

        total_api_tests = api_manual_total + api_auto_total
        total_api_bad_files = api_manual_bad + api_auto_bad

        summary_html = f"""
<div class="cloud-summary-grid">
  <div class="cloud-summary-card">
    <div class="cloud-summary-title">UI-локаторы (Playwright)</div>
    <div class="cloud-summary-main">
      <span class="cloud-summary-main-value">{ui_loc_ok}</span>
      <span class="cloud-summary-main-total">OK / {ui_loc_total_files} файлов</span>
    </div>
    <div class="cloud-summary-footer">
      Стенд: <code class="cloud-pill">{ui_base_url}</code><br/>
      {ui_loc_status_text}
    </div>
  </div>
  <div class="cloud-summary-card">
    <div class="cloud-summary-title">UI-тесты (Allure + pytest)</div>
    <div class="cloud-summary-main">
      <span class="cloud-summary-main-value">{total_ui_tests}</span>
      <span class="cloud-summary-main-total">тестов</span>
    </div>
    <div class="cloud-summary-footer">
      Файлов с нарушениями стандартов: {total_ui_bad_files}
    </div>
  </div>
  <div class="cloud-summary-card">
    <div class="cloud-summary-title">API-тесты (Allure + pytest)</div>
    <div class="cloud-summary-main">
      <span class="cloud-summary-main-value">{total_api_tests}</span>
      <span class="cloud-summary-main-total">тестов</span>
    </div>
    <div class="cloud-summary-footer">
      Файлов с нарушениями стандартов: {total_api_bad_files}
    </div>
  </div>
</div>
"""
        st.markdown(summary_html, unsafe_allow_html=True)

        if not has_any:
            st.info(
                "Пока нет данных для анализа. "
                "Сгенерируйте UI и/или API-тесты на соответствующих вкладках."
            )
            return

        # --- Детали по UI ---
        st.markdown("### Детали по UI")

        if auto_ui_dir.exists() and ui_auto_bad:
            issues_list = "".join(
                f"<li><code>{issue.file}</code> — {issue.message}</li>"
                for issue in ui_auto_issues
            )
            ui_auto_issues_html = f"""
    <details class="cloud-details">
      <summary>⚠️ Файлы с нарушениями стандартов (UI auto)</summary>
      <ul>{issues_list}</ul>
    </details>
"""
        else:
            ui_auto_issues_html = ""

        if manual_ui_dir.exists():
            ui_manual_card = f"""
  <div class="cloud-card cloud-section-card">
    <h3>Ручные тест-кейсы (Allure)</h3>
    <div class="cloud-kpi-row">
      <div class="cloud-kpi-value">{ui_manual_total}</div>
      <div class="cloud-kpi-label">Всего ручных UI-тестов</div>
    </div>
    <div class="cloud-kpi-footer">
      Файлов OK: {ui_manual_ok}, файлов с проблемами: {ui_manual_bad}
    </div>
  </div>
"""
        else:
            ui_manual_card = """
  <div class="cloud-card cloud-section-card">
    <h3>Ручные тест-кейсы (Allure)</h3>
    <p class="small-description">Ручные UI-тесты ещё не сгенерированы.</p>
  </div>
"""

        if auto_ui_dir.exists():
            ui_auto_card = f"""
  <div class="cloud-card cloud-section-card">
    <h3>Автотесты (pytest + Playwright)</h3>
    <div class="cloud-kpi-row">
      <div class="cloud-kpi-value">{ui_auto_total}</div>
      <div class="cloud-kpi-label">Всего UI-автотестов</div>
    </div>
    <div class="cloud-kpi-footer">
      Файлов OK: {ui_auto_ok}, файлов с проблемами: {ui_auto_bad}
    </div>
    {ui_auto_issues_html}
  </div>
"""
        else:
            ui_auto_card = """
  <div class="cloud-card cloud-section-card">
    <h3>Автотесты (pytest + Playwright)</h3>
    <p class="small-description">UI-автотесты ещё не сгенерированы.</p>
  </div>
"""

        ui_details_html = f"""
<div class="cloud-details-grid">
{ui_manual_card}
{ui_auto_card}
</div>
"""
        st.markdown(ui_details_html, unsafe_allow_html=True)

        # --- Детали по API ---
        st.markdown("### Детали по API")

        if manual_api_dir.exists():
            if api_manual_bad:
                issues_list = "".join(
                    f"<li><code>{issue.file}</code> — {issue.message}</li>"
                    for issue in api_manual_issues
                )
                issues_html = f"""
    <details class="cloud-details">
      <summary>⚠️ Файлы с нарушениями стандартов (API manual)</summary>
      <ul>{issues_list}</ul>
    </details>
"""
            else:
                issues_html = ""
            api_manual_html = f"""
  <div class="cloud-card cloud-section-card">
    <h3>Ручные тест-кейсы (Allure)</h3>
    <div class="cloud-kpi-row">
      <div class="cloud-kpi-value">{api_manual_total}</div>
      <div class="cloud-kpi-label">Всего ручных API-тестов</div>
    </div>
    <div class="cloud-kpi-footer">
      Файлов OK: {api_manual_ok}, файлов с проблемами: {api_manual_bad}
    </div>
    {issues_html}
  </div>
"""
        else:
            api_manual_html = """
  <div class="cloud-card cloud-section-card">
    <h3>Ручные тест-кейсы (Allure)</h3>
    <p class="small-description">Ручные API-тесты ещё не сгенерированы.</p>
  </div>
"""

        if auto_api_dir.exists():
            if api_auto_bad:
                issues_list = "".join(
                    f"<li><code>{issue.file}</code> — {issue.message}</li>"
                    for issue in api_auto_issues
                )
                issues_html = f"""
    <details class="cloud-details">
      <summary>⚠️ Файлы с нарушениями стандартов (API auto)</summary>
      <ul>{issues_list}</ul>
    </details>
"""
            else:
                issues_html = ""
            api_auto_html = f"""
  <div class="cloud-card cloud-section-card">
    <h3>Автотесты (pytest)</h3>
    <div class="cloud-kpi-row">
      <div class="cloud-kpi-value">{api_auto_total}</div>
      <div class="cloud-kpi-label">Всего API-автотестов</div>
    </div>
    <div class="cloud-kpi-footer">
      Файлов OK: {api_auto_ok}, файлов с проблемами: {api_auto_bad}
    </div>
    {issues_html}
  </div>
"""
        else:
            api_auto_html = """
  <div class="cloud-card cloud-section-card">
    <h3>Автотесты (pytest)</h3>
    <p class="small-description">API-автотесты ещё не сгенерированы.</p>
  </div>
"""

        api_details_html = f"""
<div class="cloud-details-grid">
{api_manual_html}
{api_auto_html}
</div>
"""
        st.markdown(api_details_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
