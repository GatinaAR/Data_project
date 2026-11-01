"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { Header } from "@/components/Header";
import { NewsCard } from "@/components/NewsCard";
import { Sidebar } from "@/components/Sidebar";
import { CATEGORY_COUNTS, MOCK_NEWS, WEEKLY_ACTIVITY } from "@/data/mock-news";
import type { CategoryFilter } from "@/types/news";

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<CategoryFilter>("Все новости");
  const [signInNoticeOpen, setSignInNoticeOpen] = useState(false);

  const normalizedQuery = searchQuery.trim().toLocaleLowerCase("ru-RU");
  const filteredNews = MOCK_NEWS.filter((article) => {
    const matchesCategory =
      selectedCategory === "Все новости" || article.category === selectedCategory;
    const matchesSearch = article.title.toLocaleLowerCase("ru-RU").includes(normalizedQuery);
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-[#f4f7f5] text-slate-950">
      <Header
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onSignIn={() => setSignInNoticeOpen(true)}
      />

      <div className="mx-auto grid w-full max-w-[1440px] gap-6 px-4 py-6 sm:px-6 md:grid-cols-[232px_minmax(0,1fr)] md:gap-8 md:px-8 md:py-9">
        <Sidebar
          selectedCategory={selectedCategory}
          categoryCounts={CATEGORY_COUNTS}
          onCategoryChange={setSelectedCategory}
        />

        <main id="main" className="min-w-0">
          <section className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
                Воскресенье, 1 ноября
              </p>
              <h1 className="mt-2 font-serif text-[30px] font-semibold leading-tight text-slate-950">
                Срез повестки
              </h1>
              <p className="mt-1.5 text-sm text-slate-600">
                Новости и темы, за которыми стоит следить сегодня.
              </p>
            </div>
            <div className="inline-flex items-center gap-2 pb-1 text-xs text-slate-500">
              <span className="size-2 rounded-full bg-emerald-600" aria-hidden="true" />
              Обновлено 2 минуты назад
            </div>
          </section>

          <section aria-label="Сводка" className="mt-7 grid grid-cols-3 border-y border-slate-200 py-4">
            <div className="pr-3 sm:pr-6">
              <p className="text-2xl font-semibold tabular-nums text-slate-950">{filteredNews.length}</p>
              <p className="mt-1 text-xs text-slate-500">новостей в выборке</p>
            </div>
            <div className="border-l border-slate-200 px-3 sm:px-6">
              <p className="text-2xl font-semibold tabular-nums text-slate-950">
                {new Set(filteredNews.map((article) => article.source)).size}
              </p>
              <p className="mt-1 text-xs text-slate-500">источника</p>
            </div>
            <div className="border-l border-slate-200 pl-3 sm:pl-6">
              <p className="text-2xl font-semibold tabular-nums text-slate-950">
                {new Set(filteredNews.map((article) => article.category)).size}
              </p>
              <p className="mt-1 text-xs text-slate-500">темы в ленте</p>
            </div>
          </section>

          <section aria-labelledby="activity-heading" className="border-b border-slate-200 py-5">
            <div className="mb-4 flex items-baseline justify-between gap-4">
              <h2 id="activity-heading" className="text-sm font-semibold text-slate-900">
                Публикационная активность
              </h2>
              <span className="text-xs text-slate-500">За последние 7 дней</span>
            </div>
            <div
              role="img"
              aria-label="График публикаций по дням за неделю"
              className="flex h-24 items-end gap-2 sm:gap-4"
            >
              {WEEKLY_ACTIVITY.map(({ day, count }) => (
                <div key={day} className="flex h-full flex-1 flex-col items-center justify-end gap-2">
                  <div className="flex w-full flex-1 items-end">
                    <div
                      className="mx-auto w-full max-w-10 rounded-t-sm bg-emerald-700/80 transition-colors hover:bg-emerald-800"
                      style={{ height: `${(count / 40) * 100}%` }}
                      title={`${count} публикаций`}
                    />
                  </div>
                  <span className="text-[11px] text-slate-500">{day}</span>
                </div>
              ))}
            </div>
          </section>

          <section aria-labelledby="news-heading" className="pt-6">
            <div className="mb-1 flex flex-wrap items-baseline justify-between gap-3">
              <h2 id="news-heading" className="text-lg font-semibold text-slate-950">
                Новостная лента
              </h2>
              <p className="text-xs text-slate-500" aria-live="polite">
                Найдено: {filteredNews.length}
              </p>
            </div>

            {filteredNews.length > 0 ? (
              <div className="grid grid-cols-1">
                {filteredNews.map((article) => (
                  <NewsCard key={article.id} article={article} />
                ))}
              </div>
            ) : (
              <div className="border-y border-slate-200 py-12 text-center">
                <p className="font-medium text-slate-800">Новости не найдены</p>
                <p className="mt-1 text-sm text-slate-500">
                  Измените запрос или выберите другую категорию.
                </p>
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery("");
                    setSelectedCategory("Все новости");
                  }}
                  className="mt-4 rounded px-3 py-2 text-sm font-semibold text-emerald-800 hover:bg-emerald-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700"
                >
                  Сбросить фильтры
                </button>
              </div>
            )}
          </section>
        </main>
      </div>

      {signInNoticeOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 p-4"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setSignInNoticeOpen(false);
          }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="sign-in-title"
            className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-5 shadow-xl"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 id="sign-in-title" className="font-semibold text-slate-950">
                  Вход в систему
                </h2>
                <p className="mt-2 text-sm leading-5 text-slate-600">
                  Авторизация появится после подключения Supabase Auth. Сейчас доступен демонстрационный режим.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSignInNoticeOpen(false)}
                aria-label="Закрыть окно"
                className="rounded p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700"
              >
                <X aria-hidden="true" className="size-5" />
              </button>
            </div>
            <button
              type="button"
              onClick={() => setSignInNoticeOpen(false)}
              className="mt-5 h-10 w-full rounded-md bg-emerald-800 px-4 text-sm font-semibold text-white hover:bg-emerald-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700 focus-visible:ring-offset-2"
            >
              Понятно
            </button>
          </section>
        </div>
      )}
    </div>
  );
}
