import { ArrowUpRight, Clock3 } from "lucide-react";
import type { NewsArticle, NewsCategory } from "@/types/news";

interface NewsCardProps {
  article: NewsArticle;
}

const CATEGORY_STYLES: Record<NewsCategory, string> = {
  Политика: "bg-rose-50 text-rose-800 ring-rose-700/10",
  Экономика: "bg-amber-50 text-amber-900 ring-amber-700/15",
  Спорт: "bg-sky-50 text-sky-800 ring-sky-700/10",
  Происшествия: "bg-orange-50 text-orange-900 ring-orange-700/10",
  Общество: "bg-emerald-50 text-emerald-900 ring-emerald-700/10",
  Технологии: "bg-cyan-50 text-cyan-900 ring-cyan-700/10",
  Культура: "bg-fuchsia-50 text-fuchsia-900 ring-fuchsia-700/10",
  Наука: "bg-indigo-50 text-indigo-900 ring-indigo-700/10",
  Здоровье: "bg-lime-50 text-lime-900 ring-lime-700/10",
  Другое: "bg-slate-100 text-slate-700 ring-slate-600/10",
};

const DATE_FORMATTER = new Intl.DateTimeFormat("ru-RU", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

export function NewsCard({ article }: NewsCardProps) {
  const publishedAt = DATE_FORMATTER.format(new Date(article.publishedAt));

  return (
    <article className="group border-b border-slate-200 py-5 first:pt-1 last:border-b-0">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <span className="text-xs font-semibold text-slate-600">{article.source}</span>
        <span className="size-1 rounded-full bg-slate-300" aria-hidden="true" />
        <span className="inline-flex items-center gap-1.5 text-xs text-slate-500">
          <Clock3 aria-hidden="true" className="size-3.5" strokeWidth={1.8} />
          <time dateTime={article.publishedAt}>{publishedAt}</time>
        </span>
        <span
          className={`ml-auto inline-flex items-center rounded px-2 py-1 text-[11px] font-medium ring-1 ring-inset ${CATEGORY_STYLES[article.category]}`}
        >
          {article.category}
        </span>
      </div>

      <h3 className="mt-3 max-w-4xl text-[17px] font-semibold leading-6 text-slate-950 decoration-emerald-800 decoration-2 underline-offset-4 group-hover:underline">
        {article.title}
      </h3>
      <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">{article.summary}</p>

      <div className="mt-3">
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex min-h-9 items-center gap-1.5 rounded px-2 text-sm font-semibold text-emerald-800 transition hover:bg-emerald-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700"
        >
          Читать
          <ArrowUpRight aria-hidden="true" className="size-4" strokeWidth={1.8} />
          <span className="sr-only">: {article.source}, новая вкладка</span>
        </a>
      </div>
    </article>
  );
}