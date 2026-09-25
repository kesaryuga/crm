"use client";

import { useEffect, useState } from "react";
import { Button, ErrorBox, PageHeader, Spinner, Table } from "@/components/ui";
import { apiGet } from "@/lib/api";

type Contact = {
  id: string;
  counterparty_id: string;
  full_name: string;
  position: string;
  phone: string;
  email: string;
  is_primary: boolean;
};

type CP = { id: string; full_name: string };

export default function ContactsPage() {
  const [items, setItems] = useState<Contact[]>([]);
  const [cps, setCps] = useState<CP[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const parties = await apiGet<CP[]>(`/counterparties`).catch(() => []);
      setCps(parties);
      const all: Contact[] = [];
      for (const cp of parties.slice(0, 40)) {
        const list = await apiGet<Contact[]>(`/counterparties/${cp.id}/contacts`).catch(() => []);
        all.push(...list);
      }
      setItems(all);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const names = Object.fromEntries(cps.map((c) => [c.id, c.full_name]));

  return (
    <div>
      <PageHeader title="Контакты" subtitle="Контактные лица контрагентов" />
      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading ? (
        <Table
          columns={[
            { key: "n", label: "ФИО" },
            { key: "p", label: "Должность" },
            { key: "ph", label: "Телефон" },
            { key: "e", label: "Email" },
            { key: "c", label: "Контрагент" },
          ]}
          rows={items.map((c) => [
            c.full_name,
            c.position || "—",
            c.phone || "—",
            c.email || "—",
            names[c.counterparty_id] || c.counterparty_id,
          ])}
          empty="Контактов нет"
        />
      ) : null}
    </div>
  );
}
