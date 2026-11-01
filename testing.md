# Влияние правил AI-агента на качество кода

Ниже сравнивается функция сбора RSS-новостей до и после применения правил из [`rules.md`](rules.md). Первый фрагмент намеренно показывает анти-паттерны и не предназначен для запуска. Строка `YOUR_API_KEY` — только фиктивная заглушка, не заменяйте её настоящим ключом в примере или документации.

## До применения правил

```python
import feedparser
import requests

API_KEY = "YOUR_API_KEY"
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def parse_rss(url):
    feed = feedparser.parse(url)
    articles = []

    for item in feed.entries:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"model": "some-model", "messages": [{"role": "user", "content": item.title}]},
        )
        category = response.json()["choices"][0]["message"]["content"]
        articles.append({"title": item.title, "link": item.link, "category": category})

    return articles
```

Проблемы примера: нет типизации и таймаутов, заголовок и ссылка предполагаются всегда существующими, ошибка HTTP или неожиданный ответ модели прерывают сбор. RSS-парсер связан с AI-классификацией, поэтому недоступность модели мешает получить новости. Фиктивная константа показывает место, где разработчик мог бы случайно захардкодить секрет.

## После применения правил

```python
from typing import TypedDict

import feedparser
import requests


class NewsItem(TypedDict):
    title: str
    link: str
    summary: str
    published: str


def parse_rss(feed_url: str) -> list[NewsItem]:
    """Fetch and normalize RSS entries without coupling collection to AI."""
    response = requests.get(
        feed_url,
        headers={"User-Agent": "MediaPulseNewsCollector/1.0"},
        timeout=(5, 20),
    )
    response.raise_for_status()

    feed = feedparser.parse(response.content)
    articles: list[NewsItem] = []

    for entry in feed.entries:
        title_value = entry.get("title", "")
        link_value = entry.get("link", "")
        if not isinstance(title_value, str) or not isinstance(link_value, str):
            continue

        title = title_value.strip()
        link = link_value.strip()
        if not title or not link:
            continue

        summary_value = entry.get("summary", "")
        published_value = entry.get("published", "")
        summary = summary_value.strip() if isinstance(summary_value, str) else ""
        published = published_value.strip() if isinstance(published_value, str) else ""

        articles.append(
            {
                "title": title,
                "link": link,
                "summary": summary[:1000],
                "published": published,
            }
        )

    return articles
```

Парсер теперь имеет явные типы, задаёт сетевой таймаут и проверяет обязательные поля записи. AI-классификация выполняется отдельно, после сохранения статьи: отказ модели не блокирует сбор RSS. Секреты не нужны парсеру и должны передаваться только соответствующему серверному компоненту через переменные окружения, а не храниться в исходном коде.

## Вывод

После применения правил код стал безопаснее: в нём нет настоящих API-ключей, запрос ограничен таймаутом, а ошибки HTTP не маскируются. Типизация и проверка полей делают поведение понятнее, а разделение сбора и AI-классификации повышает надёжность и упрощает тестирование каждого компонента отдельно.
