import feedparser
import pandas as pd
import matplotlib.pyplot as plt
import logging
import sqlite3
from datetime import datetime
from collections import Counter
from pathlib import Path
import re

# RSS-ленты
RSS_FEEDS = {
    "Татар-информ": "https://tatar-inform.ru/rss/",
    "Коммерсантъ":  "https://www.kommersant.ru/RSS/news.xml",
    "РИА Новости":  "https://ria.ru/export/rss2/archive/index.xml",
    "Lenta.ru":     "https://lenta.ru/rss/news",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = PROJECT_DIR / "news.db"
OUTPUT_CSV = PROJECT_DIR / "kazan_news.csv"
OUTPUT_PLOT = PROJECT_DIR / "kazan_news_plots.png"
LOG_DIR = PROJECT_DIR / "logs"

logger = logging.getLogger(__name__)

# Стоп-слова для топ-слов
STOPWORDS = set("""
и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по
только ее мне было вот от меня еще нет о из ему теперь когда даже ну вдруг ли
если уже или ни быть был него до вас нибудь опять уж вам ведь там потом себя
ничего ей может они тут где есть надо ней для мы тебя их чем была сам чтоб без
будто чего раз тоже себе под будет ж тогда кто этот того потому этого какой
совсем ним здесь этом один почти мой тем чтобы нее сейчас были куда зачем
сказать всех никогда сегодня можно при наконец два об другой хоть после над
больше тот через эти нас про всего них какая много разве три эту моя впрочем
хорошо свою этой перед иногда лучше чуть том нельзя такой им более всегда
конечно всю между это казан россия татарстан россии казани татарстана году года
лет также стал стала стали будет могут может своих своей своих рассказал заявил
глава области
""".split())


def parse_date(entry):
    """Извлекает дату публикации из RSS-записи."""
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                return datetime(*t[:6])
            except Exception:
                pass
    return entry.get("published", "")


def fetch_all_feeds():
    """Читает все RSS-ленты и возвращает список записей."""
    rows = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url, request_headers=HEADERS)
        except Exception as e:
            logger.exception("[%s] Ошибка загрузки RSS: %s", source, e)
            continue

        n = len(feed.entries)
        if n == 0:
            logger.warning("[%s] 0 записей — лента недоступна или пуста", source)
            continue

        logger.info("[%s] получено записей: %s", source, n)

        for entry in feed.entries:
            rows.append({
                "source":  source,
                "title":   entry.get("title", "").strip(),
                "link":    entry.get("link", ""),
                "summary": entry.get("summary", "")[:300],
                "date":    parse_date(entry),
            })
    return rows


def timestamp_now():
    """Возвращает локальную дату и время с указанием часового пояса."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def configure_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "kazan_news.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def initialize_database(conn, migration_time):
    """Создаёт таблицы и дополняет схему существующей базы."""
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            link TEXT UNIQUE,
            published_date TIMESTAMP,
            category TEXT
        )
    """)

    article_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(articles)").fetchall()
    }
    if "first_seen_at" not in article_columns:
        conn.execute("ALTER TABLE articles ADD COLUMN first_seen_at TEXT")
    if "last_seen_at" not in article_columns:
        conn.execute("ALTER TABLE articles ADD COLUMN last_seen_at TEXT")

    # Для старых строк время обнаружения неизвестно; фиксируем момент миграции.
    conn.execute(
        "UPDATE articles SET first_seen_at = ? WHERE first_seen_at IS NULL",
        (migration_time,),
    )
    conn.execute(
        "UPDATE articles SET last_seen_at = ? WHERE last_seen_at IS NULL",
        (migration_time,),
    )
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL,
            articles_seen INTEGER NOT NULL DEFAULT 0,
            new_articles INTEGER NOT NULL DEFAULT 0,
            existing_articles INTEGER NOT NULL DEFAULT 0,
            error_message TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL REFERENCES ingestion_runs(id),
            article_id INTEGER NOT NULL REFERENCES articles(id),
            observed_at TEXT NOT NULL,
            UNIQUE (run_id, article_id)
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_observations_run_id "
        "ON article_observations(run_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_observations_article_id "
        "ON article_observations(article_id)"
    )
    conn.commit()


def create_ingestion_run(conn, started_at):
    cursor = conn.execute(
        "INSERT INTO ingestion_runs (started_at, status) VALUES (?, ?)",
        (started_at, "running"),
    )
    conn.commit()
    return cursor.lastrowid


def save_observations(conn, run_id, rows, observed_at):
    """Сохраняет новые статьи, обновляет last_seen и связывает их с запуском."""
    new_articles = 0
    existing_articles = 0
    articles_seen = 0

    with conn:
        for row in rows:
            link = str(row.get("link") or "").strip()
            if not link:
                logger.warning("Пропущена запись без ссылки: %s", row.get("title", ""))
                continue

            published_date = row.get("date")
            if pd.notna(published_date):
                published_date = pd.Timestamp(published_date).isoformat()
            else:
                published_date = None

            cursor = conn.execute("""
                INSERT OR IGNORE INTO articles (
                    source, title, link, published_date, category,
                    first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                row.get("source", ""),
                row.get("title", ""),
                link,
                published_date,
                "Без категории",
                observed_at,
                observed_at,
            ))

            if cursor.rowcount == 1:
                article_id = cursor.lastrowid
                new_articles += 1
            else:
                conn.execute(
                    "UPDATE articles SET last_seen_at = ? WHERE link = ?",
                    (observed_at, link),
                )
                article_id = conn.execute(
                    "SELECT id FROM articles WHERE link = ?", (link,)
                ).fetchone()[0]
                existing_articles += 1

            conn.execute("""
                INSERT OR IGNORE INTO article_observations (
                    run_id, article_id, observed_at
                ) VALUES (?, ?, ?)
            """, (run_id, article_id, observed_at))
            articles_seen += 1

    return articles_seen, new_articles, existing_articles


def finish_ingestion_run(
    conn, run_id, status, articles_seen=0, new_articles=0,
    existing_articles=0, error_message=None,
):
    with conn:
        conn.execute("""
            UPDATE ingestion_runs
            SET finished_at = ?, status = ?, articles_seen = ?,
                new_articles = ?, existing_articles = ?, error_message = ?
            WHERE id = ?
        """, (
            timestamp_now(), status, articles_seen, new_articles,
            existing_articles, error_message, run_id,
        ))


def top_words(titles, n=10):
    """Топ-N самых частых слов в заголовках."""
    words = []
    for t in titles:
        for w in re.findall(r"[А-Яа-яЁёA-Za-z]{4,}", t.lower()):
            if w not in STOPWORDS:
                words.append(w)
    return Counter(words).most_common(n)


def build_plots(df):
    """4 графика ."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Количество новостей по источникам
    ax = axes[0, 0]
    counts = df["source"].value_counts()
    ax.barh(counts.index[::-1], counts.values[::-1], color="tab:blue")
    ax.set_title("Количество новостей по источникам")
    ax.set_xlabel("Число новостей")

    #  Активность по дням
    ax = axes[0, 1]
    by_day = df.dropna(subset=["date"]).set_index("date").resample("D").size()
    if len(by_day) > 0:
        ax.plot(by_day.index, by_day.values, color="tab:red", lw=1.5, marker="o")
    ax.set_title("Активность публикаций по дням")
    ax.set_ylabel("Новостей в день")
    ax.tick_params(axis="x", rotation=30)

    # Распределение по часам суток
    ax = axes[1, 0]
    hours = df.dropna(subset=["date"])["date"].dt.hour.value_counts().sort_index()
    ax.bar(hours.index, hours.values, color="tab:green")
    ax.set_title("Распределение публикаций по часам суток")
    ax.set_xlabel("Час суток")
    ax.set_ylabel("Новостей")
    ax.set_xticks(range(0, 24, 2))
    ax.grid(axis="y", alpha=0.3)

    # Топ-10 слов в заголовках
    ax = axes[1, 1]
    words = top_words(df["title"].tolist(), n=10)
    if words:
        labels, values = zip(*words)
        ax.barh(labels[::-1], values[::-1], color="tab:orange")
        ax.set_title("Топ-10 слов в заголовках")
        ax.set_xlabel("Частота")

    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT, dpi=120)
    plt.close()
    logger.info("Графики сохранены: %s", OUTPUT_PLOT)


def print_summary(df):
    """Печатает сводку в консоль."""
    logger.info("Сводка: всего новостей в текущей выборке: %s", len(df))
    logger.info("По источникам:\n%s", df["source"].value_counts().to_string())

    valid_dates = df["date"].dropna()
    if len(valid_dates) > 0:
        logger.info("Диапазон дат: %s — %s", valid_dates.min(), valid_dates.max())

    logger.info("Топ-10 слов в заголовках:")
    for w, c in top_words(df["title"].tolist(), n=10):
        logger.info("  %s: %s", w, c)


def main():
    configure_logging()
    logger.info("Запуск сбора новостей")
    started_at = timestamp_now()
    conn = sqlite3.connect(DB_PATH, timeout=30)
    run_id = None
    articles_seen = 0
    new_articles = 0
    existing_articles = 0

    try:
        initialize_database(conn, started_at)
        run_id = create_ingestion_run(conn, started_at)
        rows = fetch_all_feeds()

        if not rows:
            finish_ingestion_run(conn, run_id, "success")
            logger.warning("В этом запуске статьи не получены")
            return

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.drop_duplicates(subset="link")
        df = df[df["link"].fillna("").str.strip().ne("")]
        df = df.sort_values("date", ascending=False).reset_index(drop=True)

        observed_at = timestamp_now()
        articles_seen, new_articles, existing_articles = save_observations(
            conn, run_id, df.to_dict("records"), observed_at
        )
        df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        logger.info("CSV сохранён: %s", OUTPUT_CSV)
        logger.info(
            "Запуск %s: обработано %s, новых %s, уже известных %s",
            run_id, articles_seen, new_articles, existing_articles,
        )
        print_summary(df)
        build_plots(df)
        finish_ingestion_run(
            conn,
            run_id,
            "success",
            articles_seen,
            new_articles,
            existing_articles,
        )
        logger.info("Сбор завершён")
    except Exception as error:
        if run_id is not None:
            finish_ingestion_run(
                conn,
                run_id,
                "failed",
                articles_seen,
                new_articles,
                existing_articles,
                str(error)[:2000],
            )
        logger.exception("Ошибка запуска парсера")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()