import sys
from pathlib import Path
import shutil

import streamlit as st

# --- пути к проекту / примерам ---
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from cloudru_agent.orchestrator.orchestrator import AgentOrchestrator  # noqa: E402
from cloudru_agent.analyzers.coverage_analyzer import CoverageAnalyzer  # noqa: E402
from cloudru_agent.analyzers.standards_checker import StandardsChecker  # noqa: E402

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
        /* убрать стандартный верхний хедер Streamlit */
        header[data-testid="stHeader"] {
        display: none;
        }

        /* на всякий случай уберём ещё меню и футер Streamlit */
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

        /* фон + базовая типографика */
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

        /* карточки- панели */
        .cloud-card {
            background: var(--cloud-surface);
            border-radius: var(--cloud-radius-lg);
            padding: 1.15rem 1.25rem 1.25rem;
            border: 1px solid rgba(148, 163, 184, 0.32);
            box-shadow: 0 16px 30px rgba(15, 23, 42, 0.07);
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

        /* загрузчик файлов */
        [data-testid="stFileUploaderDropzone"] {
            border-radius: 0.9rem;
            background: var(--cloud-surface-soft);
            border: 1px dashed var(--cloud-border-strong);
        }

        [data-testid="stFileUploaderDropzone"] > div {
            color: var(--cloud-text-muted);
        }

        /* textarea и text input */
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

        /* кнопки */
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

        /* алерты / инфо-боксы */
        [data-testid="stAlert"] {
            border-radius: 0.9rem;
            border: 1px solid #BFDBFE;
            background: #EFF6FF;
        }

        /* code / экспандеры */
        pre, code {
            border-radius: 0.7rem !important;
        }

        .st-expander {
            border-radius: 0.8rem;
            border: 1px solid var(--cloud-border-subtle);
            background: var(--cloud-surface-soft);
        }

        /* метрики в аналитике */
        [data-testid="stMetricValue"] {
            font-weight: 700;
        }
        [data-testid="stMetricLabel"] {
            color: var(--cloud-text-muted);
        }
        
        .block-container h2,
        .block-container h3 {
        font-size: 1.35rem !important;   /* было больше, теперь чуть спокойнее */
        line-height: 1.25;
        margin-top: 0.2rem;
        margin-bottom: 0.9rem;
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

    # флаг, что в текущей сессии уже генерили UI-тесты и API-тесты
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

    # --- верхний уровень: два кейса ---
    ui_tab, api_tab, analytics_tab = st.tabs(
        ["UI-требования", "API-спецификация", "Аналитика"]
    )

    # =====================================================================
    # ТАБ 1. UI требования
    # =====================================================================
    with ui_tab:
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

            # кнопки: сгенерировать и очистить
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
                        orchestrator = AgentOrchestrator()
                        orchestrator.generate_ui_from_text(
                            ui_text,
                            str(GENERATED_UI_DIR),
                        )
                    st.session_state["ui_generated"] = True
                    st.success("Готово! UI-тесты сгенерированы.")

            manual_dir = GENERATED_UI_DIR / "manual_ui"
            auto_dir = GENERATED_UI_DIR / "auto_ui"

            if st.session_state["ui_generated"] and (manual_dir.exists() or auto_dir.exists()):
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
    # ТАБ 2. API Evolution Compute (заглушка под второй кейс)
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

            if not any(
                    d.exists() for d in (manual_ui_dir, auto_ui_dir, manual_api_dir, auto_api_dir)
            ):
                st.info(
                    "Пока нет данных для анализа. "
                    "Сгенерируйте UI и/или API-тесты на соответствующих вкладках."
                )
            else:
                coverage_analyzer = CoverageAnalyzer()
                standards_checker = StandardsChecker()

                # --- UI manual ---
                if manual_ui_dir.exists():
                    st.markdown("### UI: ручные тест-кейсы (Allure)")
                    cov_manual = coverage_analyzer.analyze_dir(manual_ui_dir)
                    std_manual = standards_checker.check_dir(manual_ui_dir)

                    total_manual = sum(e.total_tests for e in cov_manual.entries)
                    st.metric("Всего ручных UI-тестов", total_manual)
                    st.caption(
                        f"Файлов OK: {len(std_manual.ok_files)}, "
                        f"файлов с проблемами: {len(std_manual.issues)}"
                    )
                    if std_manual.issues:
                        with st.expander("⚠️ Файлы с нарушениями стандартов (UI manual)"):
                            for issue in std_manual.issues:
                                st.write(f"**{issue.file}** — {issue.message}")

                # --- UI auto ---
                if auto_ui_dir.exists():
                    st.markdown("### UI: автотесты (pytest + Playwright)")
                    cov_auto = coverage_analyzer.analyze_dir(auto_ui_dir)
                    std_auto = standards_checker.check_dir(auto_ui_dir)

                    total_auto = sum(e.total_tests for e in cov_auto.entries)
                    st.metric("Всего UI-автотестов", total_auto)
                    st.caption(
                        f"Файлов OK: {len(std_auto.ok_files)}, "
                        f"файлов с проблемами: {len(std_auto.issues)}"
                    )
                    if std_auto.issues:
                        with st.expander("⚠️ Файлы с нарушениями стандартов (UI auto)"):
                            for issue in std_auto.issues:
                                st.write(f"**{issue.file}** — {issue.message}")

                # --- API manual ---
                if manual_api_dir.exists():
                    st.markdown("### API: ручные тест-кейсы (Allure)")
                    cov_api_manual = coverage_analyzer.analyze_dir(manual_api_dir)
                    std_api_manual = standards_checker.check_dir(manual_api_dir)

                    total_api_manual = sum(e.total_tests for e in cov_api_manual.entries)
                    st.metric("Всего ручных API-тестов", total_api_manual)
                    st.caption(
                        f"Файлов OK: {len(std_api_manual.ok_files)}, "
                        f"файлов с проблемами: {len(std_api_manual.issues)}"
                    )
                    if std_api_manual.issues:
                        with st.expander("⚠️ Файлы с нарушениями стандартов (API manual)"):
                            for issue in std_api_manual.issues:
                                st.write(f"**{issue.file}** — {issue.message}")

                # --- API auto ---
                if auto_api_dir.exists():
                    st.markdown("### API: автотесты (pytest)")
                    cov_api_auto = coverage_analyzer.analyze_dir(auto_api_dir)
                    std_api_auto = standards_checker.check_dir(auto_api_dir)

                    total_api_auto = sum(e.total_tests for e in cov_api_auto.entries)
                    st.metric("Всего API-автотестов", total_api_auto)
                    st.caption(
                        f"Файлов OK: {len(std_api_auto.ok_files)}, "
                        f"файлов с проблемами: {len(std_api_auto.issues)}"
                    )
                    if std_api_auto.issues:
                        with st.expander("⚠️ Файлы с нарушениями стандартов (API auto)"):
                            for issue in std_api_auto.issues:
                                st.write(f"**{issue.file}** — {issue.message}")


if __name__ == "__main__":
    main()
