"use client";

import { useEffect, useState } from "react";
import {
  Button,
  ErrorBox,
  Field,
  Input,
  Modal,
  PageHeader,
  Spinner,
  Table,
  Textarea,
} from "@/components/ui";
import { apiGet, apiPost } from "@/lib/api";
import { fmtMoney } from "@/lib/format";

type Service = {
  id: string;
  code: string;
  category: string;
  name: string;
  description: string;
  unit: string;
  base_price: string;
  currency: string;
  is_active: boolean;
};

const emptyForm = {
  code: "",
  category: "",
  name: "",
  description: "",
  unit: "шт",
  base_price: "0",
  currency: "BYN",
  is_active: true,
};

export default function ServicesPage() {
  const [items, setItems] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);

  async function load() {
    setLoading(true);
    try {
      setItems(await apiGet<Service[]>(`/services`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function create() {
    try {
      await apiPost("/services", form);
      setOpen(false);
      setForm(emptyForm);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать");
    }
  }

  return (
    <div>
      <PageHeader title="Услуги" subtitle="Каталог работ и испытаний" actions={<Button onClick={() => setOpen(true)}>+ Услуга</Button>} />
      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading ? (
        <Table
          columns={[
            { key: "c", label: "Код" },
            { key: "n", label: "Наименование" },
            { key: "cat", label: "Категория" },
            { key: "u", label: "Ед." },
            { key: "p", label: "Цена" },
            { key: "a", label: "Активна" },
          ]}
          rows={items.map((s) => [
            s.code || "—",
            s.name,
            s.category || "—",
            s.unit,
            fmtMoney(s.base_price, s.currency),
            s.is_active ? "✓" : "—",
          ])}
          empty="Услуг нет"
        />
      ) : null}

      <Modal open={open} title="Новая услуга" onClose={() => setOpen(false)} wide>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Код">
            <Input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          </Field>
          <Field label="Категория">
            <Input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
          </Field>
          <Field label="Название *">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Единица">
            <Input value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
          </Field>
          <Field label="Базовая цена">
            <Input value={form.base_price} onChange={(e) => setForm({ ...form, base_price: e.target.value })} />
          </Field>
          <Field label="Валюта">
            <Input value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
          </Field>
        </div>
        <Field label="Описание">
          <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Отмена
          </Button>
          <Button onClick={create} disabled={!form.name.trim()}>
            Сохранить
          </Button>
        </div>
      </Modal>
    </div>
  );
}
