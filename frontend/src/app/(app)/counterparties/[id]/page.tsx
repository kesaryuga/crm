"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Badge,
  Button,
  Card,
  Empty,
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
import Comments from "@/components/Comments";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { CP_STATUSES, fmtDate, fmtDateTime } from "@/lib/format";

type CP = {
  id: string;
  full_name: string;
  short_name: string;
  unp: string;
  legal_address: string;
  postal_address: string;
  phone: string;
  email: string;
  website: string;
  director_name: string;
  director_position: string;
  authority_basis: string;
  bank_name: string;
  bank_bic: string;
  bank_account: string;
  status: string;
  notes: string;
};

const TABS = ["Обзор", "Контакты", "Объекты", "Задачи", "Договоры"] as const;

export default function CounterpartyPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [cp, setCp] = useState<CP | null>(null);
  const [tab, setTab] = useState<(typeof TABS)[number]>("Обзор");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [contacts, setContacts] = useState<{ id: string; full_name: string; position: string; phone: string; email: string; is_primary: boolean }[]>([]);
  const [objects, setObjects] = useState<{ id: string; name: string; address: string; status: string }[]>([]);
  const [tasks, setTasks] = useState<{ id: string; title: string; status: string; due_at: string | null; is_overdue: boolean }[]>([]);
  const [contracts, setContracts] = useState<{ id: string; number: string; status: string; total_amount: string; contract_date: string }[]>([]);
  const [editOpen, setEditOpen] = useState(false);
  const [form, setForm] = useState<Partial<CP>>({});
  const [contactOpen, setContactOpen] = useState(false);
  const [contactForm, setContactForm] = useState({ full_name: "", position: "", phone: "", email: "", is_primary: false, notes: "" });
  const [objectOpen, setObjectOpen] = useState(false);
  const [objectForm, setObjectForm] = useState({ name: "", address: "", phone: "", description: "", status: "active" });

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<CP>(`/counterparties/${id}`);
      setCp(data);
      setForm(data);
      const [c, o, t, k] = await Promise.all([
        apiGet<CP["id"] extends string ? typeof contacts : never>(`/counterparties/${id}/contacts`).catch(() => []),
        apiGet<typeof objects>(`/counterparties/${id}/objects`).catch(() => []),
        apiGet<typeof tasks>(`/tasks?counterparty_id=${id}`).catch(() => []),
        apiGet<typeof contracts>(`/contracts?counterparty_id=${id}`).catch(() => []),
      ]);
      setContacts(c as typeof contacts);
      setObjects(o as typeof objects);
      setTasks(t as typeof tasks);
      setContracts(k as typeof contracts);
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

  async function saveEdit() {
    await apiPatch(`/counterparties/${id}`, form);
    setEditOpen(false);
    await load();
  }

  async function addContact() {
    await apiPost("/contacts", { ...contactForm, counterparty_id: id });
    setContactOpen(false);
    setContactForm({ full_name: "", position: "", phone: "", email: "", is_primary: false, notes: "" });
    await load();
  }

  async function addObject() {
    await apiPost("/objects", { ...objectForm, counterparty_id: id });
    setObjectOpen(false);
    setObjectForm({ name: "", address: "", phone: "", description: "", status: "active" });
    await load();
  }

  if (loading) return <Spinner />;
  if (error) return <ErrorBox error={error} onRetry={load} />;
  if (!cp) return <Empty text="Контрагент не найден" />;

  return (
    <div>
      <PageHeader
        title={cp.full_name}
        subtitle={[cp.short_name, cp.unp && `УНП ${cp.unp}`].filter(Boolean).join(" · ")}
        actions={
          <>
            <Link href={`/tasks?counterparty_id=${id}`} className="inline-flex h-9 items-center rounded-md border border-line bg-white px-3 text-sm">
              + Задача
            </Link>
            <Button onClick={() => setEditOpen(true)}>Изменить</Button>
          </>
        }
      />

      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone={cp.status === "active" ? "ok" : "default"}>{CP_STATUSES[cp.status] || cp.status}</Badge>
        {cp.phone ? <Badge>{cp.phone}</Badge> : null}
        {cp.email ? <Badge>{cp.email}</Badge> : null}
      </div>

      <div className="mb-4 flex flex-wrap gap-1 border-b border-line">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`border-b-2 px-3 py-2 text-sm ${
              tab === t ? "border-accent font-medium text-accent" : "border-transparent text-muted"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Обзор" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Реквизиты">
            <dl className="space-y-2 text-sm">
              <div><dt className="text-muted">Юр. адрес</dt><dd>{cp.legal_address || "—"}</dd></div>
              <div><dt className="text-muted">Почтовый адрес</dt><dd>{cp.postal_address || "—"}</dd></div>
              <div><dt className="text-muted">Руководитель</dt><dd>{[cp.director_position, cp.director_name].filter(Boolean).join(", ") || "—"}</dd></div>
              <div><dt className="text-muted">Основание полномочий</dt><dd>{cp.authority_basis || "—"}</dd></div>
              <div><dt className="text-muted">Банк</dt><dd>{[cp.bank_name, cp.bank_bic, cp.bank_account].filter(Boolean).join(" · ") || "—"}</dd></div>
              <div><dt className="text-muted">Сайт</dt><dd>{cp.website || "—"}</dd></div>
            </dl>
          </Card>
          <Card title="Заметки">
            <p className="whitespace-pre-wrap text-sm">{cp.notes || "—"}</p>
          </Card>
        </div>
      ) : null}

      {tab === "Контакты" ? (
        <div>
          <div className="mb-3 flex justify-end">
            <Button onClick={() => setContactOpen(true)}>+ Контакт</Button>
          </div>
          <Table
            columns={[
              { key: "n", label: "ФИО" },
              { key: "p", label: "Должность" },
              { key: "ph", label: "Телефон" },
              { key: "e", label: "Email" },
              { key: "f", label: "Основной" },
            ]}
            rows={contacts.map((c) => [
              c.full_name,
              c.position || "—",
              c.phone || "—",
              c.email || "—",
              c.is_primary ? "✓" : "—",
            ])}
            empty="Контактов нет"
          />
        </div>
      ) : null}

      {tab === "Объекты" ? (
        <div>
          <div className="mb-3 flex justify-end">
            <Button onClick={() => setObjectOpen(true)}>+ Объект</Button>
          </div>
          <Table
            columns={[
              { key: "n", label: "Название" },
              { key: "a", label: "Адрес" },
              { key: "s", label: "Статус" },
            ]}
            rows={objects.map((o) => [
              <Link key={o.id} href={`/objects/${o.id}`} className="text-accent">
                {o.name}
              </Link>,
              o.address || "—",
              o.status,
            ])}
            empty="Объектов нет"
          />
        </div>
      ) : null}

      {tab === "Задачи" ? (
        <Table
          columns={[
            { key: "t", label: "Задача" },
            { key: "s", label: "Статус" },
            { key: "d", label: "Срок" },
          ]}
          rows={tasks.map((t) => [
            <Link key={t.id} href={`/tasks/${t.id}`} className="text-accent">
              {t.title}
            </Link>,
            t.status,
            fmtDateTime(t.due_at),
          ])}
          empty="Задач нет"
        />
      ) : null}

      {tab === "Договоры" ? (
        <Table
          columns={[
            { key: "n", label: "Номер" },
            { key: "d", label: "Дата" },
            { key: "s", label: "Статус" },
            { key: "a", label: "Сумма" },
          ]}
          rows={contracts.map((c) => [
            <Link key={c.id} href={`/contracts/${c.id}`} className="text-accent">
              {c.number}
            </Link>,
            fmtDate(c.contract_date),
            c.status,
            c.total_amount,
          ])}
          empty="Договоров нет"
        />
      ) : null}

      <Modal open={editOpen} title="Изменить контрагента" onClose={() => setEditOpen(false)} wide>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Полное наименование">
            <Input value={form.full_name || ""} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          </Field>
          <Field label="УНП">
            <Input value={form.unp || ""} onChange={(e) => setForm({ ...form, unp: e.target.value })} />
          </Field>
          <Field label="Телефон">
            <Input value={form.phone || ""} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </Field>
          <Field label="Email">
            <Input value={form.email || ""} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </Field>
          <Field label="Статус">
            <Select
              value={form.status || "active"}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
            >
              {Object.entries(CP_STATUSES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Юр. адрес">
            <Input value={form.legal_address || ""} onChange={(e) => setForm({ ...form, legal_address: e.target.value })} />
          </Field>
        </div>
        <Field label="Заметки">
          <Textarea value={form.notes || ""} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setEditOpen(false)}>
            Отмена
          </Button>
          <Button onClick={saveEdit}>Сохранить</Button>
        </div>
      </Modal>

      <Modal open={contactOpen} title="Новый контакт" onClose={() => setContactOpen(false)}>
        <div className="grid gap-3">
          <Field label="ФИО *">
            <Input value={contactForm.full_name} onChange={(e) => setContactForm({ ...contactForm, full_name: e.target.value })} />
          </Field>
          <Field label="Должность">
            <Input value={contactForm.position} onChange={(e) => setContactForm({ ...contactForm, position: e.target.value })} />
          </Field>
          <Field label="Телефон">
            <Input value={contactForm.phone} onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })} />
          </Field>
          <Field label="Email">
            <Input value={contactForm.email} onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })} />
          </Field>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setContactOpen(false)}>
            Отмена
          </Button>
          <Button onClick={addContact} disabled={!contactForm.full_name.trim()}>
            Сохранить
          </Button>
        </div>
      </Modal>

      <Modal open={objectOpen} title="Новый объект" onClose={() => setObjectOpen(false)}>
        <div className="grid gap-3">
          <Field label="Название *">
            <Input value={objectForm.name} onChange={(e) => setObjectForm({ ...objectForm, name: e.target.value })} />
          </Field>
          <Field label="Адрес">
            <Input value={objectForm.address} onChange={(e) => setObjectForm({ ...objectForm, address: e.target.value })} />
          </Field>
          <Field label="Телефон">
            <Input value={objectForm.phone} onChange={(e) => setObjectForm({ ...objectForm, phone: e.target.value })} />
          </Field>
          <Field label="Описание">
            <Textarea value={objectForm.description} onChange={(e) => setObjectForm({ ...objectForm, description: e.target.value })} />
          </Field>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setObjectOpen(false)}>
            Отмена
          </Button>
          <Button onClick={addObject} disabled={!objectForm.name.trim()}>
            Сохранить
          </Button>
        </div>
      </Modal>

      <div className="mt-4">
        <Comments entityType="counterparty" entityId={id} />
      </div>
    </div>
  );
}
