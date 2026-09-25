"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { Empty, ErrorBox, PageHeader, Spinner, Table } from "@/components/ui";
import { apiGet } from "@/lib/api";

type Hit = {
  entity_type: string;
  entity_id: string;
  title: string;
  subtitle?: string;
};

function SearchInner() {
  const params = useSearchParams();
  const q = params.get("q") || "";
  const [items, setItems] = useState<Hit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!q) return;
    setLoading(true);
    apiGet<Hit[] | { items?: Hit[]; results?: Hit[] }>(`/search?q=${encodeURIComponent(q)}`)
      .then((data) => {
        if (Array.isArray(data)) setItems(data);
        else setItems(data.items || data.results || []);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Ошибка"))
      .finally(() => setLoading(false));
  }, [q]);

  return (
    <div>
      <PageHeader title="Поиск" subtitle={q ? `Запрос: ${q}` : "Введите запрос в строке сверху"} />
      {error ? <ErrorBox error={error} /> : null}
      {loading ? <Spinner /> : null}
      {!loading && !error && !items.length ? <Empty text="Ничего не найдено" /> : null}
      {!loading && items.length ? (
        <Table
          columns={[
            { key: "t", label: "Тип" },
            { key: "n", label: "Название" },
            { key: "s", label: "Дополнительно" },
          ]}
          rows={items.map((h) => [
            h.entity_type,
            <Link key={h.entity_id} href={linkFor(h)} className="text-accent">
              {h.title}
            </Link>,
            h.subtitle || "—",
          ])}
        />
      ) : null}
    </div>
  );
}

function linkFor(h: Hit): string {
  const t = h.entity_type.toLowerCase();
  if (t.includes("counter") || t.includes("контраг")) return `/counterparties/${h.entity_id}`;
  if (t.includes("contract") || t.includes("договор")) return `/contracts/${h.entity_id}`;
  if (t.includes("task") || t.includes("задач")) return `/tasks/${h.entity_id}`;
  return "/dashboard";
}

export default function SearchPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <SearchInner />
    </Suspense>
  );
}
