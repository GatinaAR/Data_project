import feedparser
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter
import re

# RSS-ленты
RSS_FEEDS = {
    "Татар-информ": "https://tatar-inform.ru/rss/",
    "Коммерсантъ":  "https://www.kommersant.ru/RSS/news.xml",
    "РИА Новости":  "https://ria.ru/export/rss2/archive/index.xml",
    "Lenta.ru":     "https://lenta.ru/rss/news",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

OUTPUT_CSV  = "kazan_news.csv"
OUTPUT_PLOT = "kazan_news_plots.png"

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
            print(f"[{source}] Ошибка: {e}")
            continue

        n = len(feed.entries)
        if n == 0:
            print(f"[{source}] 0 записей — лента недоступна или пуста")
            continue

        print(f"[{source}] получено: {n} записей")

        for entry in feed.entries:
            rows.append({
                "source":  source,
                "title":   entry.get("title", "").strip(),
                "link":    entry.get("link", ""),
                "summary": entry.get("summary", "")[:300],
                "date":    parse_date(entry),
            })
    return rows


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
    print(f"\nГрафики сохранены: {OUTPUT_PLOT}")


def print_summary(df):
    """Печатает сводку в консоль."""
    print("\nСВОДКА")
    print(f"Всего новостей: {len(df)}")
    print(f"\nПо источникам:")
    print(df["source"].value_counts().to_string())

    valid_dates = df["date"].dropna()
    if len(valid_dates) > 0:
        print(f"\nДиапазон дат: {valid_dates.min()} → {valid_dates.max()}")

    print(f"\nТоп-10 слов в заголовках:")
    for w, c in top_words(df["title"].tolist(), n=10):
        print(f"  {w}: {c}")


def main():
    print("Сбор новостей\n")
    rows = fetch_all_feeds()

    if not rows:
        print("\nНе удалось получить новости.")
        return

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.drop_duplicates(subset="link")
    df = df.sort_values("date", ascending=False).reset_index(drop=True)

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    import sqlite3
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            link TEXT UNIQUE,
            published_date TIMESTAMP,
            category TEXT
        )
    ''')
    inserted = 0
    for _, row in df.iterrows():
        # Явно преобразуем дату в строку, чтобы избежать конфликтов
        pub_date = row['date']
        if pd.notna(pub_date):
            pub_date = pub_date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            pub_date = None
            
        cursor.execute('''
            INSERT OR IGNORE INTO articles (source, title, link, published_date, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (row['source'], row['title'], row['link'], pub_date, 'Без категории'))
        inserted += 1
    conn.commit()
    conn.close()
    print(f"В базу данных добавлено записей: {inserted}")
    # --------------------------------
    print(f"\nCSV сохранён: {OUTPUT_CSV}")

    print_summary(df)
    build_plots(df)
    print("\nГотово")


if __name__ == "__main__":
    main()