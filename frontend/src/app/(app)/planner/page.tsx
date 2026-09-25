"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Badge, ErrorBox, PageHeader, Spinner } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { PRIORITIES, TASK_STATUSES, TASK_TYPES, fmtDate } from "@/lib/format";

type Item = {
  id: string;
  title: string;
  due_at: string | null;
  status: string;
  priority: string;
  task_type: string;
  assignee_user_id: string | null;
  is_overdue: boolean;
};

function dayKey(d: Date) {
  return d.toISOString().slice(0, 10);
}

export default function PlannerPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cursor, setCursor] = useState(() => new Date());
  const [upcoming, setUpcoming] = useState<Item[]>([]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const start = new Date(cursor);
      start.setDate(start.getDate() - start.getDay() + 1); // Monday
      const end = new Date(start);
      end.setDate(end.getDate() + 6);
      const qs = `?date_from=${start.toISOString()}&date_to=${end.toISOString()}`;
      const [cal, up] = await Promise.all([
        apiGet<Item[]>(`/tasks/calendar${qs}`),
        apiGet<Item[]>(`/tasks/upcoming?hours=72`).catch(() => []),
      ]);
      setItems(cal);
      setUpcoming(up as Item[]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cursor]);

  const week = useMemo(() => {
    const start = new Date(cursor);
    start.setHours(0, 0, 0, 0);
    start.setDate(start.getDate() - ((start.getDay() + 6) % 7));
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      return d;
    });
  }, [cursor]);

  const byDay = useMemo(() => {
    const map: Record<string, Item[]> = {};
    for (const it of items) {
      if (!it.due_at) continue;
      const key = dayKey(new Date(it.due_at));
      (map[key] ||= []).push(it);
    }
    return map;
  }, [items]);

  return (
    <div>
      <PageHeader
        title="Планёрка"
        subtitle="Задачи по дням и ближайшие напоминания"
        actions={
          <div className="flex gap-2">
            <button
              type="button"
              className="rounded-md border border-line bg-white px-3 py-1.5 text-sm"
              onClick={() => {
                const d = new Date(cursor);
                d.setDate(d.getDate() - 7);
                setCursor(d);
              }}
            >
              ← Неделя
            </button>
            <button
              type="button"
              className="rounded-md border border-line bg-white px-3 py-1.5 text-sm"
              onClick={() => setCursor(new Date())}
            >
              Сегодня
            </button>
            <button
              type="button"
              className="rounded-md border border-line bg-white px-3 py-1.5 text-sm"
              onClick={() => {
                const d = new Date(cursor);
                d.setDate(d.getDate() + 7);
                setCursor(d);
              }}
            >
              Неделя →
            </button>
          </div>
        }
      />

      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}

      {!loading ? (
        <div className="grid gap-3 lg:grid-cols-4">
          <div className="lg:col-span-3">
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-7">
              {week.map((d) => {
                const key = dayKey(d);
                const list = byDay[key] || [];
                const isToday = key === dayKey(new Date());
                return (
                  <div
                    key={key}
                    className={`min-h-[160px] rounded-lg border p-2 ${
                      isToday ? "border-accent bg-accent/5" : "border-line bg-white"
                    }`}
                  >
                    <div className="mb-2 text-xs font-semibold text-muted">
                      {d.toLocaleDateString("ru-RU", { weekday: "short", day: "2-digit", month: "2-digit" })}
                    </div>
                    <div className="space-y-2">
                      {list.map((t) => (
                        <Link
                          key={t.id}
                          href={`/tasks/${t.id}`}
                          className={`block rounded-md border px-2 py-1.5 text-xs ${
                            t.is_overdue
                              ? "border-red-200 bg-red-50"
                              : t.status === "done"
                                ? "border-emerald-200 bg-emerald-50"
                                : "border-line bg-slate-50"
                          }`}
                        >
                          <div className="font-medium">{t.title}</div>
                          <div className="text-muted">
                            {TASK_TYPES[t.task_type] || t.task_type} · {PRIORITIES[t.priority] || t.priority}
                          </div>
                        </Link>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="space-y-3">
            <div className="rounded-xl border border-line bg-white p-3">
              <div className="mb-2 text-sm font-semibold">Напоминания (72ч)</div>
              {!upcoming.length ? (
                <p className="text-sm text-muted">Ближайших сроков нет</p>
              ) : (
                <ul className="space-y-2">
                  {upcoming.slice(0, 10).map((t) => (
                    <li key={t.id} className="text-sm">
                      <Link href={`/tasks/${t.id}`} className="font-medium text-accent">
                        {t.title}
                      </Link>
                      <div className="text-xs text-muted">
                        {fmtDate(t.due_at)} · {TASK_STATUSES[t.status] || t.status}
                      </div>
                      {t.is_overdue ? <Badge tone="danger">просрочено</Badge> : null}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="rounded-xl border border-line bg-white p-3 text-sm text-muted">
              Назначайте исполнителя в карточке задачи — придёт уведомление. Система напомнит о сроках за сутки.
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
