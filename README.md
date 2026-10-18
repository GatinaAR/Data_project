# Анализ медиа-пространства

Пайплайн для сбора публикаций из RSS, хранения новостей, категоризации с помощью ИИ и анализа медиа-пространства в Streamlit.

## Архитектура

```text
RSS-ленты
   |
   v
Сбор данных (`feedparser`)
   |
   v
SQLite: articles
   |
   +--> ИИ-категоризация (OpenRouter API через `requests`)
   |
   v
Аналитика и визуализация (`pandas`, `matplotlib`)
   |
   v
Дашборд на Streamlit
```

SQLite хранит собранные статьи и присвоенные категории. Слой категоризации читает статьи без категории, отправляет текст выбранной модели через OpenRouter и сохраняет результат обратно в БД. Дашборд читает данные, позволяет фильтровать их и строит визуализации. API-ключ хранится только в локальном `.env` или в секретах облачной платформы.

## Структура проекта

```text
Lab_and_projects/
|-- src/
|   `-- media_pipeline/
|       |-- ingestion/       # сбор и нормализация RSS-публикаций
|       |-- storage/         # схема SQLite и операции с БД
|       |-- processing/      # категоризация через OpenRouter
|       `-- dashboard/       # приложение Streamlit
|-- data/
|   |-- raw/                 # исходные выгрузки, если нужны
|   |-- processed/           # обработанные данные
|   `-- exports/             # CSV и прочие выгрузки
|-- reports/                 # графики и отчёты
|-- tests/                   # тесты парсера, БД и категоризации
|-- config/                  # несекретные настройки и RSS-источники
|-- .env.example             # шаблон переменных окружения без секретов
|-- .gitignore
|-- requirements.txt
`-- README.md
```

Это целевая схема, а не описание уже выполненного переноса. Имена модулей и функций можно уточнить при рефакторинге текущих скриптов. `sqlite3` входит в стандартную библиотеку Python, поэтому его нет в `requirements.txt`.

## Установка и запуск

Требуется Python 3.10 или новее. В PowerShell из корня проекта выполните:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Затем укажите ключ OpenRouter в `.env`. Не добавляйте `.env` в Git и не вставляйте ключ в исходный код. Для облачного деплоя задайте эти переменные в хранилище секретов платформы.

Пока скрипты остаются в корне проекта, запускайте их так:

```powershell
python .\kazan_news.py
streamlit run .\dashboard.py
python .\lab_crud.py
```

При прямом запуске `lab_crud.py` удаляет первую найденную новость. Запускайте его с осторожностью.

## Создание каталогов и перенос файлов

Команды ниже создают каркас и копируют скрипты в целевые модули. Сначала сделайте резервную копию `news.db`. После переноса нужно будет обновить импорты и пути к базе.

```powershell
$directories = @(
    'src\media_pipeline\ingestion',
    'src\media_pipeline\storage',
    'src\media_pipeline\processing',
    'src\media_pipeline\dashboard',
    'data\raw',
    'data\processed',
    'data\exports',
    'reports',
    'tests',
    'config'
)
$directories | ForEach-Object { New-Item -ItemType Directory -Force -Path $_ | Out-Null }

New-Item -ItemType File -Force -Path 'src\media_pipeline\__init__.py' | Out-Null
New-Item -ItemType File -Force -Path 'src\media_pipeline\ingestion\__init__.py' | Out-Null
New-Item -ItemType File -Force -Path 'src\media_pipeline\storage\__init__.py' | Out-Null
New-Item -ItemType File -Force -Path 'src\media_pipeline\processing\__init__.py' | Out-Null

Copy-Item '.\kazan_news.py' 'src\media_pipeline\ingestion\rss_collector.py'
Copy-Item '.\lab_crud.py' 'src\media_pipeline\storage\crud.py'
Copy-Item '.\dashboard.py' 'src\media_pipeline\dashboard\app.py'
Copy-Item '.\kazan_news.csv' 'data\exports\kazan_news.csv'
Copy-Item '.\kazan_news_plots.png' 'reports\kazan_news_plots.png'
Copy-Item '.\news.db' 'data\news.db'
```

Скрипты и данные копируются, а не перемещаются: исходники и рабочая БД остаются на месте для сравнения и отката. После обновления путей, проверки запуска и выбора единственной рабочей БД можно удалить ненужные копии вручную.

## Деплой в облако

Для деплоя задайте команду установки (`pip install -r requirements.txt`), команду запуска Streamlit и постоянное хранилище для SQLite. Перед публикацией добавьте OpenRouter API-ключ в секреты платформы. Если приложению нужны несколько параллельных экземпляров, SQLite обычно уже не подходит: рассмотрите управляемую серверную БД, например PostgreSQL.

## Настройки окружения

| Переменная | Назначение |
| --- | --- |
| `OPENROUTER_API_KEY` | Секретный ключ: задаётся локально в `.env` или в облачных секретах |
| `OPENROUTER_BASE_URL` | Базовый адрес API OpenRouter |
| `OPENROUTER_MODEL` | Идентификатор используемой модели OpenRouter |
| `OPENROUTER_TIMEOUT_SECONDS` | Таймаут HTTP-запроса к модели в секундах |
| `OPENROUTER_HTTP_REFERER` | Необязательный адрес приложения для заголовка `HTTP-Referer` |
| `OPENROUTER_APP_TITLE` | Необязательное имя приложения для заголовка `X-Title` |