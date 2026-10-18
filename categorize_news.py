import logging
import msvcrt
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIR / "news.db"
LOCK_PATH = PROJECT_DIR / "categorize_news.lock"
LOG_DIR = PROJECT_DIR / "logs"
MIGRATION_PATH = PROJECT_DIR / "migrations" / "001_add_categorization_fields.sql"

BATCH_SIZE = 3
MAX_ATTEMPTS = 3
DEFAULT_MODEL = "liquid/lfm-2.5-2.6b:free"
FALLBACK_MODELS = (
    "microsoft/phi-3-mini-128k-instruct:free",
)
AVAILABLE_MODELS = (DEFAULT_MODEL, *FALLBACK_MODELS)
RATE_LIMIT_RETRY_DELAY_SECONDS = 10
MAX_RATE_LIMIT_RETRIES = 1
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_TIMEOUT_SECONDS = 45

CATEGORIES = (
    "Политика",
    "Экономика",
    "Спорт",
    "Происшествия",
    "Общество",
    "Технологии",
    "Культура",
    "Наука",
    "Здоровье",
    "Другое",
)

SYSTEM_PROMPT = (
    "Ты - классификатор новостей. Верни ровно одно слово из списка: "
    "Политика, Экономика, Спорт, Происшествия, Общество, Технологии, "
    "Культура, Наука, Здоровье, Другое. Никаких других слов."
)

logger = logging.getLogger("news_categorizer")


def configure_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "categorize_news.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def acquire_single_instance_lock():
    """Locks one byte in a persistent file; the OS releases it when the process exits."""
    lock_file = open(LOCK_PATH, "a+b")
    lock_file.seek(0, os.SEEK_END)
    if lock_file.tell() == 0:
        lock_file.write(b"0")
        lock_file.flush()
    lock_file.seek(0)

    try:
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock_file.close()
        return None
    return lock_file


def release_single_instance_lock(lock_file):
    try:
        lock_file.seek(0)
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
    finally:
        lock_file.close()


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def verify_schema(connection):
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(articles)").fetchall()
    }
    required_columns = {
        "category_status",
        "category_attempts",
        "category_error",
        "categorized_at",
    }
    missing_columns = sorted(required_columns - columns)
    if missing_columns:
        migration_hint = (
            f"\nApply migration first: {MIGRATION_PATH}"
            if MIGRATION_PATH.exists()
            else ""
        )
        raise RuntimeError(
            "Missing columns in articles: " + ", ".join(missing_columns) + migration_hint
        )


def get_pending_articles(connection):
    return connection.execute(
        """
        SELECT id, title, category_attempts
        FROM articles
        WHERE category_status = 'pending'
        ORDER BY published_date IS NULL ASC, published_date DESC, id DESC
        LIMIT ?
        """,
        (BATCH_SIZE,),
    ).fetchall()


def request_category(title, api_key, model, base_url, timeout_seconds):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    http_referer = os.getenv("OPENROUTER_HTTP_REFERER")
    app_title = os.getenv("OPENROUTER_APP_TITLE")
    if http_referer:
        headers["HTTP-Referer"] = http_referer
    if app_title:
        headers["X-Title"] = app_title

    models = list(dict.fromkeys((model, *AVAILABLE_MODELS)))
    failures = []

    for index, current_model in enumerate(models):
        rate_limit_retries = 0
        while True:
            try:
                response = requests.post(
                    f"{base_url.rstrip('/')}/chat/completions",
                    headers=headers,
                    json={
                        "model": current_model,
                        "temperature": 0,
                        "max_tokens": 300,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"Заголовок новости:\n{title}"},
                        ],
                    },
                    timeout=(10, timeout_seconds),
                )
                if response.status_code == 429:
                    if rate_limit_retries < MAX_RATE_LIMIT_RETRIES:
                        rate_limit_retries += 1
                        logger.warning(
                            "Модель %s вернула 429, повторяю запрос через %s секунд "
                            "(попытка %s/%s)",
                            current_model,
                            RATE_LIMIT_RETRY_DELAY_SECONDS,
                            rate_limit_retries,
                            MAX_RATE_LIMIT_RETRIES,
                        )
                        time.sleep(RATE_LIMIT_RETRY_DELAY_SECONDS)
                        continue
                    raise requests.HTTPError(
                        f"OpenRouter HTTP 429 after retry: {response.text[:1000]}",
                        response=response,
                    )

                if not response.ok:
                    raise requests.HTTPError(
                        f"OpenRouter HTTP {response.status_code}: {response.text[:1000]}",
                        response=response,
                    )

                payload = response.json()
                content = payload["choices"][0]["message"]["content"]
                if isinstance(content, list):
                    content = "".join(
                        part.get("text", "")
                        for part in content
                        if isinstance(part, dict)
                    )
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("OpenRouter returned an empty or non-text category")

                category = content.strip()
                if category not in CATEGORIES:
                    raise ValueError(f"Invalid category returned by model: {category[:200]!r}")

                return category, current_model
            except (
                requests.RequestException,
                ValueError,
                KeyError,
                IndexError,
                TypeError,
            ) as error:
                failures.append(f"{current_model}: {type(error).__name__}: {error}")
                if index + 1 < len(models):
                    logger.warning(
                        "Модель %s не справилась, пробую %s. Причина: %s",
                        current_model,
                        models[index + 1],
                        error,
                    )
                break

    raise RuntimeError(
        "Все модели OpenRouter завершились ошибкой: " + " | ".join(failures)
    )


def save_category(connection, article_id, category, model):
    with connection:
        cursor = connection.execute(
            """
            UPDATE articles
            SET category = ?, category_status = 'success', category_error = NULL,
                categorized_at = ?
            WHERE id = ? AND category_status = 'pending'
            """,
            (category, utc_now(), article_id),
        )
    if cursor.rowcount == 0:
        logger.warning("Article %s was not updated (it may have changed concurrently)", article_id)
        return False
    logger.info("Article %s categorized as %s using %s", article_id, category, model)
    return True


def save_error(connection, article_id, error_text):
    with connection:
        row = connection.execute(
            """
            SELECT category_attempts
            FROM articles
            WHERE id = ? AND category_status = 'pending'
            """,
            (article_id,),
        ).fetchone()
        if row is None:
            return None, None

        attempts = int(row[0] or 0) + 1
        status = "failed" if attempts > MAX_ATTEMPTS else "pending"
        connection.execute(
            """
            UPDATE articles
            SET category_attempts = ?, category_error = ?, category_status = ?
            WHERE id = ? AND category_status = 'pending'
            """,
            (attempts, error_text[:2000], status, article_id),
        )
    return attempts, status


def process_batch(connection, api_key, model, base_url, timeout_seconds):
    articles = get_pending_articles(connection)
    if not articles:
        logger.info("No pending articles")
        return

    logger.info("Processing %s pending article(s)", len(articles))
    for article_id, title, previous_attempts in articles:
        try:
            category, used_model = request_category(
                title or "", api_key, model, base_url, timeout_seconds
            )
            save_category(connection, article_id, category, used_model)
        except Exception as error:
            attempts, status = save_error(
                connection, article_id, f"{type(error).__name__}: {error}"
            )
            if attempts is None:
                logger.warning("Article %s is no longer pending", article_id)
                continue
            logger.exception(
                "Categorization failed for article %s (attempt %s, status %s; "
                "previous attempts %s)",
                article_id,
                attempts,
                status,
                previous_attempts,
            )


def main():
    configure_logging()
    load_dotenv(dotenv_path=PROJECT_DIR / ".env")

    lock_file = acquire_single_instance_lock()
    if lock_file is None:
        logger.info("Another categorizer instance is already running; exiting")
        return 0

    connection = None
    try:
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            logger.error("OPENROUTER_API_KEY is missing in %s", PROJECT_DIR / ".env")
            return 1

        configured_model = os.getenv("OPENROUTER_MODEL", "").strip()
        if configured_model in AVAILABLE_MODELS:
            model = configured_model
        else:
            if configured_model and configured_model != "replace-with-a-supported-model-id":
                logger.warning(
                    "Модель %s не входит в разрешённый пул; использую %s",
                    configured_model,
                    DEFAULT_MODEL,
                )
            model = DEFAULT_MODEL
        base_url = os.getenv("OPENROUTER_BASE_URL", DEFAULT_BASE_URL).strip()
        timeout_seconds = int(
            os.getenv("OPENROUTER_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
        )
        if timeout_seconds <= 0:
            raise ValueError("OPENROUTER_TIMEOUT_SECONDS must be positive")

        connection = sqlite3.connect(DATABASE_PATH, timeout=30)
        connection.execute("PRAGMA busy_timeout = 30000")
        verify_schema(connection)
        process_batch(connection, api_key, model, base_url, timeout_seconds)
        return 0
    except Exception:
        logger.exception("Categorizer run failed")
        return 1
    finally:
        if connection is not None:
            connection.close()
        release_single_instance_lock(lock_file)


if __name__ == "__main__":
    raise SystemExit(main())