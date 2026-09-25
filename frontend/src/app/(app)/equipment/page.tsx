"use client";

import { useEffect, useState } from "react";
import {
  Badge,
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
import { fmtDate } from "@/lib/format";

type Equipment = {
  id: string;
  name: string;
  equipment_type: string;
  manufacturer: string;
  model: string;
  serial_number: string;
  inventory_number: string;
  status: string;
  verification_status: string;
  valid_until: string | null;
};

const emptyForm = {
  name: "",
  equipment_type: "",
  manufacturer: "",
  model: "",
  serial_number: "",
  inventory_number: "",
  measurement_range: "",
  units: "",
  status: "active",
  notes: "",
};

export default function EquipmentPage() {
  const [items, setItems] = useState<Equipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [verifOpen, setVerifOpen] = useState<string | null>(null);
  const [verif, setVerif] = useState({
    verification_date: new Date().toISOString().slice(0, 10),
    valid_until: "",
    certificate_number: "",
    verifier: "",
    notes: "",
  });

  async function load() {
    setLoading(true);
    try {
      setItems(await apiGet<Equipment[]>(`/equipment`));
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
      await apiPost("/equipment", form);
      setOpen(false);
      setForm(emptyForm);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать");
    }
  }

  async function addVerification() {
    if (!verifOpen) return;
    try {
      await apiPost(`/equipment/${verifOpen}/verifications`, {
        ...verif,
        verification_date: new Date(verif.verification_date).toISOString(),
        valid_until: new Date(verif.valid_until).toISOString(),
      });
      setVerifOpen(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось добавить поверку");
    }
  }

  const tone = (s: string) =>
    s === "valid" ? "ok" : s === "expiring" ? "warn" : s === "expired" ? "danger" : "default";

  return (
    <div>
      <PageHeader
        title="Оборудование"
        subtitle="Средства измерений и поверки"
        actions={<Button onClick={() => setOpen(true)}>+ Оборудование</Button>}
      />
      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading ? (
        <Table
          columns={[
            { key: "n", label: "Название" },
            { key: "m", label: "Модель / зав. №" },
            { key: "i", label: "Инв. №" },
            { key: "v", label: "Поверка" },
            { key: "u", label: "Действительна до" },
            { key: "a", label: "" },
          ]}
          rows={items.map((e) => [
            <div key={e.id}>
              <div className="font-medium">{e.name}</div>
              <div className="text-xs text-muted">{e.equipment_type}</div>
            </div>,
            [e.manufacturer, e.model, e.serial_number].filter(Boolean).join(" ") || "—",
            e.inventory_number || "—",
            <Badge key="v" tone={tone(e.verification_status) as "ok" | "warn" | "danger" | "default"}>
              {e.verification_status}
            </Badge>,
            fmtDate(e.valid_until),
            <Button key="a" variant="secondary" onClick={() => setVerifOpen(e.id)}>
              + Поверка
            </Button>,
          ])}
          empty="Оборудования нет"
        />
      ) : null}

      <Modal open={open} title="Новое оборудование" onClose={() => setOpen(false)} wide>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Название *">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Тип">
            <Input value={form.equipment_type} onChange={(e) => setForm({ ...form, equipment_type: e.target.value })} />
          </Field>
          <Field label="Производитель">
            <Input value={form.manufacturer} onChange={(e) => setForm({ ...form, manufacturer: e.target.value })} />
          </Field>
          <Field label="Модель">
            <Input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
          </Field>
          <Field label="Серийный №">
            <Input value={form.serial_number} onChange={(e) => setForm({ ...form, serial_number: e.target.value })} />
          </Field>
          <Field label="Инвентарный №">
            <Input
              value={form.inventory_number}
              onChange={(e) => setForm({ ...form, inventory_number: e.target.value })}
            />
          </Field>
          <Field label="Диапазон">
            <Input
              value={form.measurement_range}
              onChange={(e) => setForm({ ...form, measurement_range: e.target.value })}
            />
          </Field>
          <Field label="Единицы">
            <Input value={form.units} onChange={(e) => setForm({ ...form, units: e.target.value })} />
          </Field>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Отмена
          </Button>
          <Button onClick={create} disabled={!form.name.trim()}>
            Сохранить
          </Button>
        </div>
      </Modal>

      <Modal open={!!verifOpen} title="Добавить поверку" onClose={() => setVerifOpen(null)}>
        <div className="grid gap-3">
          <Field label="Дата поверки">
            <Input
              type="date"
              value={verif.verification_date}
              onChange={(e) => setVerif({ ...verif, verification_date: e.target.value })}
            />
          </Field>
          <Field label="Действительна до *">
            <Input type="date" value={verif.valid_until} onChange={(e) => setVerif({ ...verif, valid_until: e.target.value })} />
          </Field>
          <Field label="№ свидетельства">
            <Input
              value={verif.certificate_number}
              onChange={(e) => setVerif({ ...verif, certificate_number: e.target.value })}
            />
          </Field>
          <Field label="Организация">
            <Input value={verif.verifier} onChange={(e) => setVerif({ ...verif, verifier: e.target.value })} />
          </Field>
          <Field label="Заметки">
            <Textarea value={verif.notes} onChange={(e) => setVerif({ ...verif, notes: e.target.value })} />
          </Field>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setVerifOpen(null)}>
            Отмена
          </Button>
          <Button onClick={addVerification} disabled={!verif.valid_until}>
            Сохранить
          </Button>
        </div>
      </Modal>
    </div>
  );
}
