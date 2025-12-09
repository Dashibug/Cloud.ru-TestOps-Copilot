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
        /* фон и отступы страницы */
        .main {
            padding-top: 0.5rem;
        }

        /* кастомная шапка */
        .cloud-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0 1rem 0;
        }
        .cloud-title {
            font-size: 1.6rem;
            font-weight: 700;
            color: #00BF6F; /* фирменный зелёный Cloud.ru */
        }
        .cloud-subtitle {
            font-size: 0.9rem;
            color: #6B6B6B;
        }
        .cloud-badge {
            padding: 0.25rem 0.9rem;
            border-radius: 999px;
            background-color: #E5F8F0;
            color: #008F54;
            font-size: 0.8rem;
            font-weight: 600;
            white-space: nowrap;
        }

        /* кнопки */
        .stButton>button {
            border-radius: 999px;
            border: none;
            background: linear-gradient(90deg, #00BF6F, #00D694);
            color: white;
            font-weight: 600;
            padding: 0.45rem 1.4rem;
        }

        /* вкладки */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.25rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: 0.25rem 0.75rem;
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
          <div>
            <div class="cloud-title">Cloud.ru TestOps Copilot</div>
            <div class="cloud-subtitle">
              Генерация тест-кейсов и автотестов на базе Evolution Foundation Model
            </div>
          </div>
          <div class="cloud-badge">Hackathon · Evolution FM</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- верхний уровень: два кейса ---
    ui_tab, api_tab, analytics_tab = st.tabs(
        ["UI калькулятор цен", "API Evolution Compute (v3)", "Аналитика"]
    )

    # =====================================================================
    # ТАБ 1. UI калькулятор
    # =====================================================================
    with ui_tab:
        left, right = st.columns([1, 1])

        # левая колонка — требования
        with left:
            st.subheader("1. Описание пользовательского сценария")

            st.caption(
                "Вставьте текст требований к Cloud.ru Price Calculator "
                "или загрузите файл с описанием сценариев."
            )

            uploaded = st.file_uploader(
                "Загрузите файл с требованиями (md / txt) или введите текст ниже",
                type=["md", "txt"],
            )

            if uploaded is not None:
                ui_text = uploaded.read().decode("utf-8")
            else:
                ui_text = st.text_area(
                    "Текст требований для UI калькулятора",
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
            st.subheader("2. Сгенерированные артефакты для UI")

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
            st.subheader("1. OpenAPI-спецификация Evolution Compute v3")
            st.caption(
                "Загрузите OpenAPI 3.0 (yaml/json) для разделов VMs, Disks, Flavors "
                "или вставьте текст спецификации."
            )

            openapi_file = st.file_uploader(
                "Загрузите OpenAPI 3.0 спецификацию (yaml/json)",
                type=["yaml", "yml", "json", "txt"],
                key="openapi_uploader",
            )
            openapi_text_area = st.text_area(
                "Или вставьте сюда содержимое OpenAPI",
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
            st.subheader("2. Сгенерированные артефакты для API")

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
