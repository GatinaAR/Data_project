"use client";

import { useState } from "react";
import { Check, ChevronDown, LayoutDashboard, Newspaper } from "lucide-react";
import { NEWS_CATEGORIES } from "@/types/news";
import type { CategoryCounts, CategoryFilter } from "@/types/news";

interface SidebarProps {
  selectedCategory: CategoryFilter;
  categoryCounts: CategoryCounts;
  onCategoryChange: (category: CategoryFilter) => void;
}

const FILTERS: { label: CategoryFilter; icon?: typeof LayoutDashboard }[] = [
  { label: "Все новости", icon: LayoutDashboard },
  ...NEWS_CATEGORIES.map((label) => ({ label })),
];

export function Sidebar({
  selectedCategory,
  categoryCounts,
  onCategoryChange,
}: SidebarProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <aside className="w-full md:w-[232px] md:shrink-0">
      <div className="md:sticky md:top-[88px]">
        <button
          type="button"
          aria-expanded={isOpen}
          aria-controls="news-category-filters"
          onClick={() => setIsOpen((open) => !open)}
          className="flex min-h-11 w-full items-center justify-between rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700 md:hidden"
        >
          <span className="flex items-center gap-2">
            <Newspaper aria-hidden="true" className="size-4 text-slate-500" strokeWidth={1.8} />
            Фильтр по категориям
          </span>
          <ChevronDown
            aria-hidden="true"
            className={`size-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
          />
        </button>

        <div
          id="news-category-filters"
          className={`${isOpen ? "block" : "hidden"} mt-3 rounded-md border border-slate-200 bg-white p-3 md:mt-0 md:block md:border-0 md:bg-transparent md:p-0`}
        >
          <div className="mb-3 hidden items-center justify-between px-1 md:flex">
            <h2 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Категории
            </h2>
            <Newspaper
              aria-hidden="true"
              className="size-4 text-slate-400"
              strokeWidth={1.8}
            />
          </div>

          <nav aria-label="Категории" className="space-y-1">
            {FILTERS.map(({ label, icon: Icon }) => {
              const isSelected = selectedCategory === label;

              return (
                <button
                  key={label}
                  type="button"
                  aria-pressed={isSelected}
                  onClick={() => {
                    onCategoryChange(label);
                    setIsOpen(false);
                  }}
                  className={`flex min-h-10 w-full items-center gap-2.5 rounded-md px-3 text-left text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700 ${
                    isSelected
                      ? "bg-emerald-900 text-white"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
                  }`}
                >
                  {Icon ? (
                    <Icon aria-hidden="true" className="size-4 shrink-0" strokeWidth={1.8} />
                  ) : (
                    <span className="size-4 shrink-0" aria-hidden="true" />
                  )}
                  <span className="min-w-0 flex-1 truncate">{label}</span>
                  <span
                    className={`min-w-5 text-right text-xs tabular-nums ${
                      isSelected ? "text-emerald-100" : "text-slate-400"
                    }`}
                  >
                    {categoryCounts[label]}
                  </span>
                  {isSelected && <Check aria-hidden="true" className="size-3.5" />}
                </button>
              );
            })}
          </nav>

          <div className="mt-4 border-t border-slate-200 pt-4 md:mt-6">
            <p className="px-1 text-xs leading-5 text-slate-500">
              Категории помогают быстро выделить нужную часть новостной повестки.
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}