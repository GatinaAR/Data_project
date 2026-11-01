import { NEWS_CATEGORIES } from "@/types/news";
import type { CategoryCounts, NewsArticle } from "@/types/news";

export const MOCK_NEWS: NewsArticle[] = [
  {
    id: "news-1",
    title: "Банк России сохранил ключевую ставку на прежнем уровне",
    source: "РБК",
    publishedAt: "2026-11-01T10:42:00+03:00",
    category: "Экономика",
    summary: "Регулятор объяснил решение динамикой инфляции и оценкой внутреннего спроса.",
    url: "https://example.com/news/1",
  },
  {
    id: "news-2",
    title: "В регионе открыли новый маршрут общественного транспорта",
    source: "Татар-информ",
    publishedAt: "2026-11-01T10:18:00+03:00",
    category: "Общество",
    summary: "Маршрут связал несколько жилых районов с центром города.",
    url: "https://example.com/news/2",
  },
  {
    id: "news-3",
    title: "Казанская команда одержала победу в домашнем матче",
    source: "Спорт-Экспресс",
    publishedAt: "2026-11-01T09:56:00+03:00",
    category: "Спорт",
    summary: "Исход встречи определил гол, забитый во втором тайме.",
    url: "https://example.com/news/3",
  },
  {
    id: "news-4",
    title: "Ученые представили новую систему раннего обнаружения паводков",
    source: "Наука РФ",
    publishedAt: "2026-11-01T09:31:00+03:00",
    category: "Наука",
    summary: "Разработка объединяет спутниковые снимки и данные датчиков уровня воды.",
    url: "https://example.com/news/4",
  },
  {
    id: "news-5",
    title: "Городской музей открыл выставку архивной фотохроники",
    source: "Коммерсантъ",
    publishedAt: "2026-11-01T09:04:00+03:00",
    category: "Культура",
    summary: "Экспозиция рассказывает об истории города через фотографии нескольких десятилетий.",
    url: "https://example.com/news/5",
  },
];

export const CATEGORY_COUNTS = NEWS_CATEGORIES.reduce(
  (counts, category) => {
    counts[category] = MOCK_NEWS.filter((article) => article.category === category).length;
    return counts;
  },
  { "Все новости": MOCK_NEWS.length } as CategoryCounts,
);

export const WEEKLY_ACTIVITY = [
  { day: "Пн", count: 18 },
  { day: "Вт", count: 25 },
  { day: "Ср", count: 21 },
  { day: "Чт", count: 32 },
  { day: "Пт", count: 27 },
  { day: "Сб", count: 38 },
  { day: "Вс", count: 31 },
];
