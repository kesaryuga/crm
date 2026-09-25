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
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { CONTRACT_STATUSES, fmtDate, fmtMoney } from "@/lib/format";

type Item = {
  id: string;
  name_snapshot: string;
  unit_snapshot: string;
  quantity: string;
  unit_price: string;
  subtotal: string;
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
  items: Item[];
  valid_from: string | null;
  valid_to: string | null;
};

type Service = { id: string; name: string; unit: string; base_price: string };

export default function ContractPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [contract, setContract] = useState<Contract | null>(null);
  const [services, setServices] = useState<Service[]>([]);
  const [cpName, setCpName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [itemOpen, setItemOpen] = useState(false);
  const [itemForm, setItemForm] = useState({
    service_id: "",
    name_snapshot: "",
    unit_snapshot: "шт",
    quantity: "1",
    unit_price: "0",
  });
  const [statusOpen, setStatusOpen] = useState(false);
  const [nextStatus, setNextStatus] = useState("active");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<Contract>(`/contracts/${id}`);
      setContract(data);
      setNextStatus(data.status);
      const [svcs, cps] = await Promise.all([
        apiGet<Service[]>(`/services`).catch(() => []),
        apiGet<{ id: string; full_name: string }[]>(`/counterparties`).catch(() => []),
      ]);
      setServices(svcs);
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

  async function addItem() {
    await apiPost(`/contracts/${id}/items`, {
      ...itemForm,
      service_id: itemForm.service_id || null,
      quantity: itemForm.quantity,
      unit_price: itemForm.unit_price,
    });
    setItemOpen(false);
    setItemForm({ service_id: "", name_snapshot: "", unit_snapshot: "шт", quantity: "1", unit_price: "0" });
    await load();
  }

  async function changeStatus() {
    await apiPatch(`/contracts/${id}`, { status: nextStatus });
    setStatusOpen(false);
    await load();
  }

  if (loading) return <Spinner />;
  if (error) return <ErrorBox error={error} onRetry={load} />;
  if (!contract) return <Empty text="Договор не найден" />;

  return (
    <div>
      <PageHeader
        title={`Договор ${[contract.series, contract.number].filter(Boolean).join(" ")}`}
        subtitle={`${fmtDate(contract.contract_date)} · ${cpName}`}
        actions={
          <>
            <Button variant="secondary" onClick={() => setStatusOpen(true)}>
              Статус
            </Button>
            <Button onClick={() => setItemOpen(true)}>+ Услуга</Button>
          </>
        }
      />

      <div className="mb-4">
        <Badge tone={contract.status === "active" ? "ok" : contract.status === "draft" ? "warn" : "default"}>
          {CONTRACT_STATUSES[contract.status] || contract.status}
        </Badge>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Условия">
          <dl className="space-y-2 text-sm">
            <div>
              <dt className="text-muted">Срок</dt>
              <dd>
                {fmtDate(contract.valid_from)} — {fmtDate(contract.valid_to)}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Валюта</dt>
              <dd>{contract.currency}</dd>
            </div>
            <div>
              <dt className="text-muted">Комментарий</dt>
              <dd>{contract.notes || "—"}</dd>
            </div>
          </dl>
        </Card>
        <Card title="Суммы">
          <dl className="space-y-2 text-sm">
            <div>
              <dt className="text-muted">Без НДС</dt>
              <dd className="text-lg font-semibold">{fmtMoney(contract.subtotal, contract.currency)}</dd>
            </div>
            <div>
              <dt className="text-muted">Итого</dt>
              <dd className="text-lg font-semibold text-accent">{fmtMoney(contract.total_amount, contract.currency)}</dd>
            </div>
            {contract.amount_in_words ? (
              <div>
                <dt className="text-muted">Прописью</dt>
                <dd>{contract.amount_in_words}</dd>
              </div>
            ) : null}
          </dl>
        </Card>
        <Card title="Документы">
          <p className="text-sm text-muted">
            Генерация DOCX — через раздел «Шаблоны» (загрузка Word-шаблона и формирование).
          </p>
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

      <Modal open={itemOpen} title="Добавить услугу" onClose={() => setItemOpen(false)}>
        <div className="grid gap-3">
          <Field label="Услуга из справочника">
            <Select
              value={itemForm.service_id}
              onChange={(e) => {
                const s = services.find((x) => x.id === e.target.value);
                setItemForm({
                  ...itemForm,
                  service_id: e.target.value,
                  name_snapshot: s?.name || itemForm.name_snapshot,
                  unit_snapshot: s?.unit || itemForm.unit_snapshot,
                  unit_price: s?.base_price || itemForm.unit_price,
                });
              }}
            >
              <option value="">— вручную —</option>
              {services.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Наименование *">
            <Input
              value={itemForm.name_snapshot}
              onChange={(e) => setItemForm({ ...itemForm, name_snapshot: e.target.value })}
            />
          </Field>
          <div className="grid grid-cols-3 gap-2">
            <Field label="Кол-во">
              <Input
                value={itemForm.quantity}
                onChange={(e) => setItemForm({ ...itemForm, quantity: e.target.value })}
              />
            </Field>
            <Field label="Ед.">
              <Input
                value={itemForm.unit_snapshot}
                onChange={(e) => setItemForm({ ...itemForm, unit_snapshot: e.target.value })}
              />
            </Field>
            <Field label="Цена">
              <Input
                value={itemForm.unit_price}
                onChange={(e) => setItemForm({ ...itemForm, unit_price: e.target.value })}
              />
            </Field>
          </div>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setItemOpen(false)}>
            Отмена
          </Button>
          <Button onClick={addItem} disabled={!itemForm.name_snapshot.trim()}>
            Добавить
          </Button>
        </div>
      </Modal>

      <Modal open={statusOpen} title="Изменить статус" onClose={() => setStatusOpen(false)}>
        <Field label="Статус">
          <Select value={nextStatus} onChange={(e) => setNextStatus(e.target.value)}>
            {Object.entries(CONTRACT_STATUSES).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </Select>
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setStatusOpen(false)}>
            Отмена
          </Button>
          <Button onClick={changeStatus}>Сохранить</Button>
        </div>
      </Modal>
    </div>
  );
}
