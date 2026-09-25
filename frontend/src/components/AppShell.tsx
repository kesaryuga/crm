"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

type Me = {
  email: string;
  first_name: string;
  last_name: string;
  role: string | null;
  permissions: string[];
};

const NAV: { section: string; items: { href: string; label: string }[] }[] = [
  {
    section: "Обзор",
    items: [{ href: "/dashboard", label: "Главная" }],
  },
  {
    section: "CRM",
    items: [
      { href: "/counterparties", label: "Контрагенты" },
      { href: "/objects", label: "Объекты" },
      { href: "/contacts", label: "Контакты" },
    ],
  },
  {
    section: "Работа",
    items: [
      { href: "/tasks", label: "Задачи" },
      { href: "/works", label: "Испытания" },
    ],
  },
  {
    section: "Документы",
    items: [
      { href: "/contracts", label: "Договоры" },
      { href: "/protocols", label: "Протоколы" },
      { href: "/templates", label: "Шаблоны" },
    ],
  },
  {
    section: "Справочники",
    items: [
      { href: "/services", label: "Услуги" },
      { href: "/equipment", label: "Оборудование" },
    ],
  },
];

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [search, setSearch] = useState("");
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    apiGet<Me>("/auth/me")
      .then(setMe)
      .catch(() => {
        window.location.href = "/login";
      });
  }, []);

  async function logout() {
    await fetch("/api/v1/auth/logout", { method: "POST", credentials: "include" });
    window.location.href = "/login";
  }

  function onSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = search.trim();
    if (q) router.push(`/search?q=${encodeURIComponent(q)}`);
  }

  return (
    <div className="min-h-screen bg-paper">
      <div className="flex min-h-screen">
        <aside
          className={`fixed inset-y-0 left-0 z-40 w-60 transform border-r border-line bg-white transition-transform lg:static lg:translate-x-0 ${
            navOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="flex h-14 items-center border-b border-line px-4">
            <Link href="/dashboard" className="text-lg font-semibold tracking-tight">
              CRM · КИТ-лаб
            </Link>
          </div>
          <nav className="space-y-5 overflow-y-auto p-3 pb-24">
            {NAV.map((group) => (
              <div key={group.section}>
                <div className="mb-1 px-2 text-[11px] font-semibold uppercase tracking-wide text-muted">
                  {group.section}
                </div>
                <div className="space-y-0.5">
                  {group.items.map((item) => {
                    const active = pathname === item.href || pathname.startsWith(item.href + "/");
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setNavOpen(false)}
                        className={`block rounded-md px-2.5 py-2 text-sm ${
                          active ? "bg-accent/10 font-medium text-accent" : "text-ink hover:bg-slate-100"
                        }`}
                      >
                        {item.label}
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-line bg-white px-4">
            <button
              type="button"
              className="rounded-md border border-line px-2 py-1 text-sm lg:hidden"
              onClick={() => setNavOpen((v) => !v)}
            >
              Меню
            </button>
            <form onSubmit={onSearch} className="min-w-0 flex-1 max-w-md">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Поиск: УНП, название, телефон…"
                className="h-9 w-full rounded-md border border-line bg-slate-50 px-3 text-sm outline-none focus:border-accent focus:bg-white"
              />
            </form>
            <div className="ml-auto flex items-center gap-3">
              {me ? (
                <div className="hidden text-right sm:block">
                  <div className="text-sm font-medium leading-tight">
                    {me.last_name} {me.first_name}
                  </div>
                  <div className="text-xs text-muted">{me.role || "—"}</div>
                </div>
              ) : null}
              <button
                type="button"
                onClick={logout}
                className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-slate-50"
              >
                Выйти
              </button>
            </div>
          </header>
          <main className="mx-auto w-full max-w-7xl flex-1 p-4 sm:p-6">{children}</main>
        </div>
      </div>
    </div>
  );
}
