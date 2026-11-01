import { fireEvent, render, screen } from "@testing-library/react";
import { Header } from "@/components/Header";
import { NewsCard } from "@/components/NewsCard";
import { Sidebar } from "@/components/Sidebar";
import type { CategoryCounts, NewsArticle } from "@/types/news";

const article: NewsArticle = {
  id: "news-test-1",
  title: "Тестовый заголовок новости",
  source: "Тестовый источник",
  publishedAt: "2026-11-01T10:00:00+03:00",
  category: "Экономика",
  summary: "Краткое описание тестовой новости.",
  url: "https://example.com/news/test",
};

const categoryCounts: CategoryCounts = {
  "Все новости": 1,
  Политика: 0,
  Экономика: 1,
  Спорт: 0,
  Происшествия: 0,
  Общество: 0,
  Технологии: 0,
  Культура: 0,
  Наука: 0,
  Здоровье: 0,
  Другое: 0,
};

describe("dashboard components", () => {
  it("Header renders the Media Pulse title", () => {
    render(
      <Header searchQuery="" onSearchChange={() => {}} onSignIn={() => {}} />,
    );

    expect(screen.getByText("Медиа-Пульс")).toBeInTheDocument();
  });

  it("NewsCard renders the provided article title", () => {
    render(<NewsCard article={article} />);

    expect(screen.getByRole("heading", { name: article.title })).toBeInTheDocument();
  });

  it("Sidebar calls the category callback when a category button is clicked", () => {
    const onCategoryChange = jest.fn();
    render(
      <Sidebar
        selectedCategory="Все новости"
        categoryCounts={categoryCounts}
        onCategoryChange={onCategoryChange}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Экономика/ }));

    expect(onCategoryChange).toHaveBeenCalledWith("Экономика");
  });
});