"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Badge,
  Card,
  Empty,
  ErrorBox,
  PageHeader,
  Spinner,
  StatCard,
} from "@/components/ui";
import { apiGet } from "@/lib/api";
import { fmtDateTime, TASK_STATUSES } from "@/lib/format";

type Dashboard = {
  tasks_today?: number;
  overdue_tasks?: number;
  works_today?: number;
  draft_protocols?: number;
  my_tasks?: {
    id: string;
    title: string;
    status: string;
    due_at: string | null;
    is_overdue: boolean;
    priority: string;
  }[];
  recent?: { id: string; action: string; created_at?: string }[];
  notifications?: { id: string; title?: string; message?: string; created_at?: string }[];
};

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const d = await apiGet<Dashboard>("/dashboard");
      setData(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div>
      <PageHeader
        title="Главная"
        subtitle="Обзор работы на сегодня"
        actions={
          <>
            <Link href="/tasks" className="inline-flex h-9 items-center rounded-md border border-line bg-white px-3 text-sm">
              Задачи
            </Link>
            <Link href="/counterparties" className="inline-flex h-9 items-center rounded-md bg-accent px-3 text-sm font-medium text-white">
              Контрагенты
            </Link>
          </>
        }
      />

      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}

      {data ? (
        <div className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Задачи сегодня" value={data.tasks_today ?? 0} />
            <StatCard label="Просрочено" value={data.overdue_tasks ?? 0} />
            <StatCard label="Испытания сегодня" value={data.works_today ?? 0} />
            <StatCard label="Протоколы-черновики" value={data.draft_protocols ?? 0} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Мои задачи">
              {!data.my_tasks?.length ? (
                <Empty text="Задач нет" />
              ) : (
                <ul className="divide-y divide-line">
                  {data.my_tasks.map((t) => (
                    <li key={t.id} className="flex items-start justify-between gap-3 py-2">
                      <div>
                        <Link href={`/tasks/${t.id}`} className="font-medium text-ink hover:text-accent">
                          {t.title}
                        </Link>
                        <div className="text-xs text-muted">
                          {fmtDateTime(t.due_at)}
                          {t.is_overdue ? " · просрочено" : ""}
                        </div>
                      </div>
                      <Badge tone={t.is_overdue ? "danger" : t.status === "done" ? "ok" : "info"}>
                        {TASK_STATUSES[t.status] || t.status}
                      </Badge>
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card title="Уведомления">
              {!data.notifications?.length ? (
                <Empty text="Новых уведомлений нет" />
              ) : (
                <ul className="divide-y divide-line">
                  {data.notifications.slice(0, 8).map((n) => (
                    <li key={n.id} className="py-2 text-sm">
                      <div className="font-medium">{n.title || n.message || "Уведомление"}</div>
                      <div className="text-xs text-muted">{fmtDateTime(n.created_at)}</div>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>

          <Card title="Последние действия">
            {!data.recent?.length ? (
              <Empty text="Пока нет событий" />
            ) : (
              <ul className="divide-y divide-line text-sm">
                {data.recent.slice(0, 10).map((r) => (
                  <li key={r.id} className="py-2">
                    <span className="text-muted">{fmtDateTime(r.created_at)}</span> — {r.action}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      ) : null}
    </div>
  );
}
