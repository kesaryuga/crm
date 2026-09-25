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

export function CommentsInline({
  entityType,
  entityId,
  limit = 2,
}: {
  entityType: string;
  entityId: string;
  limit?: number;
}) {
  const [items, setItems] = useState<CommentRow[]>([]);
  const [open, setOpen] = useState(false);
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await apiGet<CommentRow[]>(
        `/comments?entity_type=${encodeURIComponent(entityType)}&entity_id=${encodeURIComponent(entityId)}`,
      );
      setItems(Array.isArray(data) ? data : []);
    } catch {
      setItems([]);
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
      setOpen(true);
    } finally {
      setSaving(false);
    }
  }

  const shown = open ? items : items.slice(0, limit);

  return (
    <div className="rounded-lg border border-amber-100 bg-amber-50/60 px-3 py-2 text-sm">
      <div className="mb-1 flex items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-amber-800">
          Комментарии{items.length ? ` · ${items.length}` : ""}
        </span>
        {items.length > limit ? (
          <button
            type="button"
            className="text-xs text-accent underline"
            onClick={() => setOpen((v) => !v)}
          >
            {open ? "Свернуть" : `Показать все (${items.length})`}
          </button>
        ) : null}
      </div>
      {loading ? <span className="text-xs text-muted">…</span> : null}
      {!loading && !items.length ? (
        <p className="text-xs text-muted">Комментариев нет — можно добавить ниже</p>
      ) : null}
      <ul className="space-y-1">
        {shown.map((c) => (
          <li key={c.id} className="rounded bg-white/70 px-2 py-1">
            <div className="whitespace-pre-wrap">{c.body}</div>
            <div className="text-[11px] text-muted">{fmtDateTime(c.created_at)}</div>
          </li>
        ))}
      </ul>
      <div className="mt-2 flex gap-2">
        <Textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Комментарий…"
          className="min-h-[48px] flex-1 bg-white"
        />
        <Button onClick={add} disabled={saving || !body.trim()} className="self-end">
          {saving ? "…" : "Отправить"}
        </Button>
      </div>
    </div>
  );
}

export default function Comments({
  entityType,
  entityId,
  title = "Комментарии",
}: {
  entityType: string;
  entityId: string;
  title?: string;
}) {
  return (
    <section className="rounded-xl border border-line bg-white">
      <header className="border-b border-line px-4 py-3 text-sm font-semibold">{title}</header>
      <div className="p-4">
        <CommentsInline entityType={entityType} entityId={entityId} limit={20} />
      </div>
    </section>
  );
}
