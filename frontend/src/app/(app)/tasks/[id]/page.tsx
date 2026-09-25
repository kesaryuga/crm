"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Badge,
  Button,
  Card,
  Empty,
  ErrorBox,
  Field,
  Input,
  PageHeader,
  Select,
  Spinner,
  Textarea,
} from "@/components/ui";
import Comments from "@/components/Comments";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { PRIORITIES, TASK_STATUSES, TASK_TYPES, fmtDateTime } from "@/lib/format";

type Task = {
  id: string;
  title: string;
  description: string;
  task_type: string;
  status: string;
  priority: string;
  due_at: string | null;
  is_overdue: boolean;
  assignee_user_id: string | null;
  creator_user_id: string | null;
};

export default function TaskPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const router = useRouter();
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<Task>(`/tasks/${id}`);
      setTask(data);
      // открытие задачи: новая → в работе
      if (data.status === "new") {
        const updated = await apiPatch<Task>(`/tasks/${id}`, { status: "in_progress" });
        setTask(updated);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (id) void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function complete() {
    setSaving(true);
    try {
      await apiPost(`/tasks/${id}/complete`, {});
      router.push("/tasks");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось завершить");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <Spinner />;
  if (error && !task) return <ErrorBox error={error} onRetry={load} />;
  if (!task) return <Empty text="Задача не найдена" />;

  return (
    <div>
      <PageHeader
        title={task.title}
        subtitle={`${TASK_TYPES[task.task_type] || task.task_type} · ${PRIORITIES[task.priority] || task.priority}`}
        actions={
          task.status !== "completed" && task.status !== "done" && task.status !== "cancelled" ? (
            <Button onClick={complete} disabled={saving}>
              {saving ? "Сохраняем…" : "Готово"}
            </Button>
          ) : (
            <Badge tone="ok">Выполнена</Badge>
          )
        }
      />
      {error ? <ErrorBox error={error} /> : null}
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone={task.status === "completed" || task.status === "done" ? "ok" : task.is_overdue ? "danger" : "info"}>
          {TASK_STATUSES[task.status] || task.status}
        </Badge>
        {task.is_overdue ? <Badge tone="danger">просрочено</Badge> : null}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Описание">
          <p className="whitespace-pre-wrap text-sm">{task.description || "—"}</p>
        </Card>
        <Card title="Параметры">
          <dl className="space-y-2 text-sm">
            <div>
              <dt className="text-muted">Срок</dt>
              <dd>{fmtDateTime(task.due_at)}</dd>
            </div>
            <div>
              <dt className="text-muted">Статус</dt>
              <dd>{TASK_STATUSES[task.status] || task.status}</dd>
            </div>
          </dl>
        </Card>
      </div>

      <div className="mt-4">
        <Comments entityType="task" entityId={id} />
      </div>
    </div>
  );
}
