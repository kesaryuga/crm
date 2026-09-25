"use client";

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
import { apiDelete, apiGet, apiPatch, apiPost } from "@/lib/api";
import { CONTRACT_STATUSES, fmtDate, fmtMoney } from "@/lib/format";

type Act = {
  id: string;
  title: string;
  act_number: string;
  act_date: string | null;
  due_date: string | null;
  amount: string;
  status: string;
  notes: string;
};

type Item = {
  id: string;
  name_snapshot: string;
  unit_snapshot: string;
  quantity: string;
  unit_price: string;
  total: string;
};

type Contract = {
  id: string;
  number: string;
  series: string;
  contract_date: string;
  counterparty_id: string;
  status: string;
  currency: string;
  subtotal: string;
  vat_amount: string;
  total_amount: string;
  amount_in_words: string;
  notes: string;
  valid_from: string | null;
  valid_to: string | null;
  execution_days: number;
  execution_term: string;
  parts_count: number;
  items: Item[];
  acts: Act[];
};

const ACT_STATUSES: Record<string, string> = {
  planned: "Запланирован",
  in_progress: "Выполняется",
  signed: "Подписан",
  done: "Закрыт",
};

const emptyAct = {
  title: "",
  act_number: "",
  act_date: "",
  due_date: "",
  amount: "0",
  status: "planned",
  notes: "",
};

export default function ContractPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [contract, setContract] = useState<Contract | null>(null);
  const [cpName, setCpName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [editOpen, setEditOpen] = useState(false);
  const [actOpen, setActOpen] = useState(false);
  const [actForm, setActForm] = useState(emptyAct);
  const [form, setForm] = useState<Partial<Contract>>({});
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<Contract>(`/contracts/${id}`);
      setContract(data);
      setForm(data);
      const cps = await apiGet<{ id: string; full_name: string }[]>(`/counterparties`).catch(() => []);
      setCpName(cps.find((c) => c.id === data.counterparty_id)?.full_name || data.counterparty_id);
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
    setSaving(true);
    try {
      await apiPatch(`/contracts/${id}`, {
        series: form.series,
        number: form.number,
        status: form.status,
        notes: form.notes,
        execution_days: Number(form.execution_days) || 0,
        execution_term: form.execution_term || "",
        parts_count: Number(form.parts_count) || 1,
        contract_date: form.contract_date,
        valid_from: form.valid_from || null,
        valid_to: form.valid_to || null,
      });
      setEditOpen(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  async function addAct() {
    setSaving(true);
    try {
      await apiPost(`/contracts/${id}/acts`, {
        title: actForm.title,
        act_number: actForm.act_number,
        act_date: actForm.act_date ? new Date(actForm.act_date).toISOString() : null,
        due_date: actForm.due_date ? new Date(actForm.due_date).toISOString() : null,
        amount: actForm.amount || "0",
        status: actForm.status,
        notes: actForm.notes,
      });
      setActOpen(false);
      setActForm(emptyAct);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось добавить акт");
    } finally {
      setSaving(false);
    }
  }

  async function removeAct(aid: string) {
    await apiDelete(`/contracts/${id}/acts/${aid}`);
    await load();
  }

  if (loading) return <Spinner />;
  if (error && !contract) return <ErrorBox error={error} onRetry={load} />;
  if (!contract) return <Empty text="Договор не найден" />;

  return (
    <div>
      <PageHeader
        title={`Договор ${[contract.series, contract.number].filter(Boolean).join(" ")}`}
        subtitle={`${fmtDate(contract.contract_date)} · ${cpName}`}
        actions={
          <>
            <Button variant="secondary" onClick={() => setEditOpen(true)}>
              Редактировать
            </Button>
            <Button onClick={() => setActOpen(true)}>+ Акт / часть</Button>
          </>
        }
      />

      {error ? <ErrorBox error={error} /> : null}

      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone={contract.status === "active" ? "ok" : contract.status === "draft" ? "warn" : "default"}>
          {CONTRACT_STATUSES[contract.status] || contract.status}
        </Badge>
        {contract.execution_days > 0 ? (
          <Badge tone="info">Срок: {contract.execution_days} дн.</Badge>
        ) : null}
        {contract.execution_term ? <Badge>{contract.execution_term}</Badge> : null}
        <Badge>Частей: {contract.parts_count}</Badge>
      </div>

      <div className="grid gap-4 lg:grid-cols-4">
        <Card title="Суммы">
          <div className="space-y-3 text-sm">
            <div>
              <div className="text-muted">Без НДС</div>
              <div className="text-xl font-semibold">{fmtMoney(contract.subtotal, contract.currency)}</div>
            </div>
            <div>
              <div className="text-muted">НДС</div>
              <div className="text-lg">{fmtMoney(contract.vat_amount, contract.currency)}</div>
            </div>
            <div>
              <div className="text-muted">Итого</div>
              <div className="text-2xl font-semibold text-accent">
                {fmtMoney(contract.total_amount, contract.currency)}
              </div>
            </div>
            {contract.amount_in_words ? (
              <p className="text-xs text-muted">{contract.amount_in_words}</p>
            ) : null}
          </div>
        </Card>

        <Card title="Сроки">
          <dl className="space-y-2 text-sm">
            <div>
              <dt className="text-muted">Действует с</dt>
              <dd>{fmtDate(contract.valid_from)}</dd>
            </div>
            <div>
              <dt className="text-muted">Действует до</dt>
              <dd>{fmtDate(contract.valid_to)}</dd>
            </div>
            <div>
              <dt className="text-muted">На исполнение</dt>
              <dd>
                {contract.execution_days > 0
                  ? `${contract.execution_days} календарных дней`
                  : contract.execution_term || "—"}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Частей / актов</dt>
              <dd>{contract.parts_count}</dd>
            </div>
          </dl>
        </Card>

        <Card title="Комментарий">
          <p className="text-sm whitespace-pre-wrap">{contract.notes || "—"}</p>
        </Card>

        <Card title="Документы">
          <p className="text-sm text-muted">Генерация DOCX — раздел «Шаблоны».</p>
        </Card>
      </div>

      <div className="mt-4">
        <Card title="Услуги по договору">
          <Table
            columns={[
              { key: "n", label: "Наименование" },
              { key: "q", label: "Кол-во" },
              { key: "p", label: "Цена" },
              { key: "t", label: "Сумма" },
            ]}
            rows={contract.items.map((it) => [
              it.name_snapshot,
              `${it.quantity} ${it.unit_snapshot}`,
              fmtMoney(it.unit_price, contract.currency),
              fmtMoney(it.total, contract.currency),
            ])}
            empty="Услуги не добавлены"
          />
        </Card>
      </div>

      <div className="mt-4">
        <Card
          title="Части и акты"
          actions={
            <Button variant="secondary" onClick={() => setActOpen(true)}>
              + Акт
            </Button>
          }
        >
          <Table
            columns={[
              { key: "t", label: "Название" },
              { key: "n", label: "№ акта" },
              { key: "d", label: "Срок" },
              { key: "a", label: "Сумма" },
              { key: "s", label: "Статус" },
              { key: "x", label: "" },
            ]}
            rows={(contract.acts || []).map((a) => [
              a.title,
              a.act_number || "—",
              fmtDate(a.due_date),
              fmtMoney(a.amount, contract.currency),
              <Badge key="s" tone={a.status === "done" || a.status === "signed" ? "ok" : "default"}>
                {ACT_STATUSES[a.status] || a.status}
              </Badge>,
              <Button key="x" variant="ghost" onClick={() => removeAct(a.id)}>
                Удалить
              </Button>,
            ])}
            empty="Актов / частей пока нет"
          />
        </Card>
      </div>

      <Modal open={editOpen} title="Редактировать договор" onClose={() => setEditOpen(false)} wide>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Серия">
            <Input value={form.series || ""} onChange={(e) => setForm({ ...form, series: e.target.value })} />
          </Field>
          <Field label="Номер">
            <Input value={form.number || ""} onChange={(e) => setForm({ ...form, number: e.target.value })} />
          </Field>
          <Field label="Дата договора">
            <Input
              type="date"
              value={(form.contract_date || "").slice(0, 10)}
              onChange={(e) => setForm({ ...form, contract_date: e.target.value })}
            />
          </Field>
          <Field label="Статус">
            <Select value={form.status || "draft"} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              {Object.entries(CONTRACT_STATUSES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Действует с">
            <Input
              type="date"
              value={(form.valid_from || "").slice(0, 10)}
              onChange={(e) => setForm({ ...form, valid_from: e.target.value })}
            />
          </Field>
          <Field label="Действует до">
            <Input
              type="date"
              value={(form.valid_to || "").slice(0, 10)}
              onChange={(e) => setForm({ ...form, valid_to: e.target.value })}
            />
          </Field>
          <Field label="Срок исполнения, дней">
            <Input
              type="number"
              min={0}
              value={form.execution_days ?? 0}
              onChange={(e) => setForm({ ...form, execution_days: Number(e.target.value) })}
            />
          </Field>
          <Field label="Условие срока (текст)">
            <Input
              value={form.execution_term || ""}
              placeholder="например: 30 рабочих дней"
              onChange={(e) => setForm({ ...form, execution_term: e.target.value })}
            />
          </Field>
          <Field label="Количество частей / актов">
            <Input
              type="number"
              min={1}
              value={form.parts_count ?? 1}
              onChange={(e) => setForm({ ...form, parts_count: Number(e.target.value) })}
            />
          </Field>
        </div>
        <Field label="Комментарий">
          <Textarea value={form.notes || ""} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setEditOpen(false)}>
            Отмена
          </Button>
          <Button onClick={saveEdit} disabled={saving}>
            {saving ? "Сохраняем…" : "Сохранить"}
          </Button>
        </div>
      </Modal>

      <Modal open={actOpen} title="Новый акт / часть" onClose={() => setActOpen(false)} wide>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Название *">
            <Input value={actForm.title} onChange={(e) => setActForm({ ...actForm, title: e.target.value })} />
          </Field>
          <Field label="Номер акта">
            <Input value={actForm.act_number} onChange={(e) => setActForm({ ...actForm, act_number: e.target.value })} />
          </Field>
          <Field label="Дата акта">
            <Input type="date" value={actForm.act_date} onChange={(e) => setActForm({ ...actForm, act_date: e.target.value })} />
          </Field>
          <Field label="Срок">
            <Input type="date" value={actForm.due_date} onChange={(e) => setActForm({ ...actForm, due_date: e.target.value })} />
          </Field>
          <Field label="Сумма">
            <Input value={actForm.amount} onChange={(e) => setActForm({ ...actForm, amount: e.target.value })} />
          </Field>
          <Field label="Статус">
            <Select value={actForm.status} onChange={(e) => setActForm({ ...actForm, status: e.target.value })}>
              {Object.entries(ACT_STATUSES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        <Field label="Заметки">
          <Textarea value={actForm.notes} onChange={(e) => setActForm({ ...actForm, notes: e.target.value })} />
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setActOpen(false)}>
            Отмена
          </Button>
          <Button onClick={addAct} disabled={saving || !actForm.title.trim()}>
            Добавить
          </Button>
        </div>
      </Modal>
    </div>
  );
}
