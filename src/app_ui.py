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


EXAMPLES_DIR = SRC_DIR / "examples"
DEFAULT_UI_REQ_FILE = EXAMPLES_DIR / "ui_calc_requirements_text.md"
GENERATED_UI_DIR = SRC_DIR / "generated" / "from_text"


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

    # флаг, что в текущей сессии уже генерили UI-тесты
    if "ui_generated" not in st.session_state:
        st.session_state["ui_generated"] = False

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
    ui_tab, api_tab = st.tabs(["UI калькулятор цен", "API Evolution Compute (v3)"])

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
        st.subheader("API Evolution Compute: генерация тестов (в разработке)")
        st.caption(
            "Здесь будет генерация ручных кейсов и pytest-тестов по OpenAPI 3.0 "
            "для разделов VMs, Disks, Flavors."
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            openapi_file = st.file_uploader(
                "Загрузите OpenAPI 3.0 спецификацию (yaml/json)",
                type=["yaml", "yml", "json"],
                key="openapi_uploader",
            )
            st.text_area(
                "Или вставьте сюда фрагмент OpenAPI со схемой операции",
                height=250,
                key="openapi_text",
            )

            if st.button("Сгенерировать API-тесты"):
                st.warning(
                    "Поддержка API-кейса сейчас в разработке. "
                    "В бэкенде уже есть каркас для OpenAPI-парсера и генераторов; "
                    "на защите мы покажем этот сценарий как следующий шаг."
                )

        with col2:
            st.info(
                "План по API-кейсу:\n"
                "• разобрать OpenAPI 3.0 на операции VMs / Disks / Flavors;\n"
                "• сгенерировать ручные кейсы в формате Allure TestOps as Code;\n"
                "• сгенерировать pytest-тесты с проверками кода ответа и схем;\n"
                "• использовать Evolution FM для подбора позитивных и негативных сценариев."
            )


if __name__ == "__main__":
    main()
