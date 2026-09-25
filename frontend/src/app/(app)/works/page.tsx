"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Badge,
  Button,
  ErrorBox,
  Field,
  Input,
  Modal,
  PageHeader,
  Select,
  Spinner,
  Table,
  Textarea,
} from "@/components/ui";
import { apiGet, apiPost } from "@/lib/api";
import { WORK_STATUSES, fmtDate } from "@/lib/format";

type Work = {
  id: string;
  number: string;
  work_date: string;
  counterparty_id: string;
  object_id: string | null;
  status: string;
  notes: string;
  test_type: string;
  address: string;
  parameters_count: number;
  sample_count: number;
  method: string;
  contact_person: string;
  contact_phone: string;
};

type CP = { id: string; full_name: string };

const TEST_TYPES = [
  { value: "", label: "Все типы" },
  { value: "geotech", label: "Геотехнические" },
  { value: "materials", label: "Испытания материалов" },
  { value: "chemistry", label: "Химические анализы" },
  { value: "electrical", label: "Электроизмерения" },
  { value: "metrology", label: "Метрология / поверка" },
  { value: "environment", label: "Экология / среда" },
  { value: "other", label: "Другое" },
];

const TYPE_LABELS = Object.fromEntries(TEST_TYPES.map((t) => [t.value, t.label]));

const emptyForm = {
  number: "",
  work_date: new Date().toISOString().slice(0, 10),
  counterparty_id: "",
  object_id: "",
  status: "planned",
  notes: "",
  test_type: "other",
  address: "",
  parameters_count: "0",
  sample_count: "0",
  method: "",
  contact_person: "",
  contact_phone: "",
};

export default function WorksPage() {
  const [items, setItems] = useState<Work[]>([]);
  const [cps, setCps] = useState<CP[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [testType, setTestType] = useState("");
  const [sort, setSort] = useState("date_desc");
  const [saving, setSaving] = useState(false);

  const names = Object.fromEntries(cps.map((c) => [c.id, c.full_name]));

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (status) params.set("status", status);
      if (testType) params.set("test_type", testType);
      if (sort) params.set("sort", sort);
      const [list, parties] = await Promise.all([
        apiGet<Work[]>(`/works${params.toString() ? `?${params}` : ""}`),
        apiGet<CP[]>(`/counterparties`).catch(() => []),
      ]);
      setItems(list);
      setCps(parties);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, testType, sort]);

  async function create() {
    setSaving(true);
    try {
      await apiPost("/works", {
        ...form,
        work_date: new Date(form.work_date).toISOString(),
        object_id: form.object_id || null,
        parameters_count: Number(form.parameters_count) || 0,
        sample_count: Number(form.sample_count) || 0,
      });
      setOpen(false);
      setForm(emptyForm);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать");
    } finally {
      setSaving(false);
    }
  }

  const cols = useMemo(
    () => [
      { key: "n", label: "Номер" },
      { key: "d", label: "Дата" },
      { key: "t", label: "Тип испытаний" },
      { key: "a", label: "Адрес" },
      { key: "p", label: "Пар." },
      { key: "s", label: "Обр." },
      { key: "st", label: "Статус" },
      { key: "c", label: "Контрагент" },
    ],
    [],
  );

  return (
    <div>
      <PageHeader
        title="Испытания / работы"
        subtitle="Номера вручную, со сбросом года"
        actions={<Button onClick={() => setOpen(true)}>+ Испытание</Button>}
      />

      <div className="mb-4 flex flex-wrap gap-2">
        <Input
          placeholder="Поиск: номер, адрес, метод, контакт…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
          className="w-72"
        />
        <Select value={testType} onChange={(e) => setTestType(e.target.value)} className="w-52">
          {TEST_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </Select>
        <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-48">
          <option value="">Все статусы</option>
          {Object.entries(WORK_STATUSES).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
        <Select value={sort} onChange={(e) => setSort(e.target.value)} className="w-52">
          <option value="date_desc">Дата ↓</option>
          <option value="date_asc">Дата ↑</option>
          <option value="number_asc">Номер ↑</option>
          <option value="number_desc">Номер ↓</option>
          <option value="params_desc">Параметров ↓</option>
          <option value="params_asc">Параметров ↑</option>
        </Select>
        <Button variant="secondary" onClick={load}>
          Найти
        </Button>
      </div>

      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading ? (
        <Table
          columns={cols}
          rows={items.map((w) => [
            <span key={w.id} className="font-medium">
              {w.number}
            </span>,
            fmtDate(w.work_date),
            TYPE_LABELS[w.test_type] || w.test_type || "—",
            w.address || "—",
            w.parameters_count || "—",
            w.sample_count || "—",
            <Badge key="s" tone={w.status === "done" ? "ok" : "info"}>
              {WORK_STATUSES[w.status] || w.status}
            </Badge>,
            names[w.counterparty_id] || w.counterparty_id,
          ])}
          empty="Испытаний нет"
        />
      ) : null}

      <Modal open={open} title="Новое испытание" onClose={() => setOpen(false)} wide>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Номер *">
            <Input value={form.number} onChange={(e) => setForm({ ...form, number: e.target.value })} />
          </Field>
          <Field label="Дата *">
            <Input
              type="date"
              value={form.work_date}
              onChange={(e) => setForm({ ...form, work_date: e.target.value })}
            />
          </Field>
          <Field label="Контрагент *">
            <Select value={form.counterparty_id} onChange={(e) => setForm({ ...form, counterparty_id: e.target.value })}>
              <option value="">— выберите —</option>
              {cps.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.full_name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Тип испытаний">
            <Select value={form.test_type} onChange={(e) => setForm({ ...form, test_type: e.target.value })}>
              {TEST_TYPES.filter((t) => t.value).map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Адрес объекта">
            <Input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          </Field>
          <Field label="Метод / ГОСТ">
            <Input value={form.method} onChange={(e) => setForm({ ...form, method: e.target.value })} />
          </Field>
          <Field label="Количество параметров">
            <Input
              type="number"
              min={0}
              value={form.parameters_count}
              onChange={(e) => setForm({ ...form, parameters_count: e.target.value })}
            />
          </Field>
          <Field label="Количество проб / образцов">
            <Input
              type="number"
              min={0}
              value={form.sample_count}
              onChange={(e) => setForm({ ...form, sample_count: e.target.value })}
            />
          </Field>
          <Field label="Контактное лицо">
            <Input value={form.contact_person} onChange={(e) => setForm({ ...form, contact_person: e.target.value })} />
          </Field>
          <Field label="Телефон">
            <Input value={form.contact_phone} onChange={(e) => setForm({ ...form, contact_phone: e.target.value })} />
          </Field>
          <Field label="Статус">
            <Select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              {Object.entries(WORK_STATUSES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        <Field label="Заметки">
          <Textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Отмена
          </Button>
          <Button onClick={create} disabled={saving || !form.number || !form.counterparty_id}>
            {saving ? "Сохраняем…" : "Создать"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
