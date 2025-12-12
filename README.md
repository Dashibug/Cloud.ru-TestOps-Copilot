# ☁️  Cloud.ru TestOps Copilot

ИИ-ассистент для генерация ручных тест-кейсов, UI- и API-автотестов с использованием Evolution Foundation Models.
Автоматически разбирает UI-требования и OpenAPI-спеки,  
генерирует ручные тесты, полноценные автотесты, выполняет ревью, автоматически исправляет 
найденные дефекты в тестах и проверяет валидность локаторов на реальном продукте.


<img width="1071" height="699" alt="image" src="https://github.com/user-attachments/assets/86a7eeb0-5046-497d-9e6d-54cb39c446e2" />



### Что умеет ИИ-ассистент

---

#### Генерация ручных тестов (Allure TestOps as Code)

- По UI-требованиям и OpenAPI спецификации.

#### Генерация автоматических UI-тестов (pytest + Playwright)

- Построение шагов по шаблону **AAA (Arrange–Act–Assert)**
- Генерация кода Playwright
- LLM-ревью
- Автофикс кода

#### Генерация API-автотестов (pytest + requests)

- Извлечение параметров из OpenAPI
- Формирование тела запроса, path- и query-параметров
- Добавление проверок:
  - `status_code`
  - JSON-структуры

#### LLM-ревью и автофиксация автотестов

Две модели:

- **Генератор** - пишет тесты
- **Ревизор** - проверяет и предлагает правки

Система автоматически переписывает тесты, если они содержат дефекты.

## Инструкция по установке и локальному запуску

#### 1. Клонирование и установка зависимостей

```bash
git clone <repo_url>
cd <repo_folder>

python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows
# .venv\Scripts\activate

pip install -U pip
pip install -r requirements.txt
```

#### 2. Установка браузеров Playwright

```bash
python -m playwright install --with-deps
```
> Если Playwright нужен только для анализа локаторов, 
> но вы не планируете прогон UI-тестов - всё равно рекомендуется установить браузеры, 
> иначе валидатор локаторов не сможет открыть страницу.

#### 3. Настройка переменных окружения
Создайте файл .env в корне проекта и приложите:
```bash
# ===== LLM / Evolution Foundation Models =====
API_KEY=<your_key>
EVOLUTION_GEN_MODEL=Qwen/Qwen3-Coder-480B-A35B-Instruct
EVOLUTION_REVIEW_MODEL=Qwen/Qwen3-Next-80B-A3B-Instruct
EVOLUTION_BASE_URL=https://foundation-models.api.cloud.ru/v1
```

#### 4. Запуск приложения
```bash
streamlit run src/app_ui.py
```

## Структура результатов

После генерации файлы появляются в следующих директориях:

```text
src/generated/from_text/
  manual_ui/   # ручные UI тест-кейсы (Allure)
  auto_ui/     # UI автотесты (pytest + Playwright)

src/generated/api_from_openapi/
  manual_api/  # ручные API тест-кейсы (Allure)
  auto_api/    # API автотесты (pytest)
```

