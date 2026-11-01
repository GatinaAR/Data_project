import { Activity, CircleUserRound, Search } from "lucide-react";

interface HeaderProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  onSignIn: () => void;
}

function SearchField({
  searchQuery,
  onSearchChange,
  className = "",
}: Pick<HeaderProps, "searchQuery" | "onSearchChange"> & {
  className?: string;
}) {
  return (
    <label className={`relative block ${className}`}>
      <span className="sr-only">Поиск по заголовкам новостей</span>
      <Search
        aria-hidden="true"
        className="pointer-events-none absolute left-3.5 top-1/2 size-[18px] -translate-y-1/2 text-slate-400"
        strokeWidth={1.8}
      />
      <input
        type="search"
        value={searchQuery}
        onChange={(event) => onSearchChange(event.target.value)}
        placeholder="Найти новость или тему"
        className="h-11 w-full rounded-md border border-slate-200 bg-slate-50 pl-10 pr-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-emerald-700 focus:bg-white focus:ring-2 focus:ring-emerald-700/10"
      />
    </label>
  );
}

export function Header({ searchQuery, onSearchChange, onSignIn }: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/95 backdrop-blur">
      <div className="mx-auto flex min-h-16 max-w-[1440px] items-center justify-between gap-5 px-4 sm:px-6 lg:px-8">
        <a href="#main" className="flex shrink-0 items-center gap-3" aria-label="Медиа-Пульс — на главную">
          <span className="flex size-9 items-center justify-center rounded-md bg-emerald-800 text-white">
            <Activity aria-hidden="true" className="size-5" strokeWidth={2} />
          </span>
          <span>
            <span className="block text-[15px] font-semibold leading-5 text-slate-950">Медиа-Пульс</span>
            <span className="hidden text-[11px] leading-4 text-slate-500 sm:block">Мониторинг повестки</span>
          </span>
        </a>

        <SearchField
          searchQuery={searchQuery}
          onSearchChange={onSearchChange}
          className="hidden w-full max-w-[520px] md:block"
        />

        <button
          type="button"
          onClick={onSignIn}
          className="inline-flex h-10 shrink-0 items-center gap-2 rounded-md border border-slate-200 px-3.5 text-sm font-medium text-slate-700 transition hover:border-emerald-800/30 hover:bg-emerald-50 hover:text-emerald-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700"
        >
          <CircleUserRound aria-hidden="true" className="size-[17px]" strokeWidth={1.8} />
          <span>Войти</span>
        </button>
      </div>

      <div className="px-4 pb-3 sm:px-6 md:hidden">
        <SearchField searchQuery={searchQuery} onSearchChange={onSearchChange} />
      </div>
    </header>
  );
}