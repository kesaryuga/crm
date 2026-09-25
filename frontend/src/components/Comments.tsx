"use client";

import { useEffect, useState } from "react";
import { Button, Spinner, Textarea } from "@/components/ui";
import { apiGet, apiPost } from "@/lib/api";
import { fmtDateTime } from "@/lib/format";

export type CommentRow = {
  id: string;
  entity_type: string;
  entity_id: string;
  body: string;
  is_executor_note: boolean;
  author_user_id: string | null;
  created_at?: string;
};

export default function Comments({
  entityType,
  entityId,
  title = "Комментарии",
}: {
  entityType: string;
  entityId: string;
  title?: string;
}) {
  const [items, setItems] = useState<CommentRow[]>([]);
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<CommentRow[]>(
        `/comments?entity_type=${encodeURIComponent(entityType)}&entity_id=${encodeURIComponent(entityId)}`,
      );
      setItems(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (entityId) void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entityType, entityId]);

  async function add() {
    if (!body.trim()) return;
    setSaving(true);
    try {
      await apiPost("/comments", {
        entity_type: entityType,
        entity_id: entityId,
        body: body.trim(),
        is_executor_note: false,
      });
      setBody("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="rounded-xl border border-line bg-white">
      <header className="border-b border-line px-4 py-3 text-sm font-semibold">{title}</header>
      <div className="space-y-3 p-4">
        <div className="flex flex-col gap-2">
          <Textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Написать комментарий…"
            className="min-h-[72px]"
          />
          <div className="flex justify-end">
            <Button onClick={add} disabled={saving || !body.trim()}>
              {saving ? "Сохраняем…" : "Отправить"}
            </Button>
          </div>
        </div>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        {loading ? <Spinner /> : null}
        {!loading && !items.length ? (
          <p className="text-sm text-muted">Комментариев пока нет</p>
        ) : null}
        <ul className="space-y-2">
          {items.map((c) => (
            <li key={c.id} className="rounded-md border border-line bg-slate-50 px-3 py-2 text-sm">
              <div className="whitespace-pre-wrap">{c.body}</div>
              <div className="mt-1 text-xs text-muted">{fmtDateTime(c.created_at)}</div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
