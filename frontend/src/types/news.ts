export const NEWS_CATEGORIES = [
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
] as const;

export type NewsCategory = (typeof NEWS_CATEGORIES)[number];
export type CategoryFilter = "Все новости" | NewsCategory;

export interface NewsArticle {
  id: string;
  title: string;
  source: string;
  publishedAt: string;
  category: NewsCategory;
  summary: string;
  url: string;
}

export type CategoryCounts = Record<CategoryFilter, number>;