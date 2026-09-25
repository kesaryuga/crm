"use client";

import { useEffect, useRef, useState } from "react";
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
} from "@/components/ui";
import { apiGet } from "@/lib/api";

type Template = {
  id: string;
  code: string;
  name: string;
  document_type: string;
  version: number;
  is_active: boolean;
  placeholders: string[];
};

const DOC_TYPES = [
  { value: "contract", label: "Договор" },
  { value: "protocol", label: "Протокол" },
  { value: "act", label: "Акт" },
  { value: "commercial", label: "Коммерческое предложение" },
  { value: "other", label: "Другое" },
];

export default function TemplatesPage() {
  const [items, setItems] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [docType, setDocType] = useState("contract");
  const [file, setFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setItems(await apiGet<Template[]>(`/templates`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function upload() {
    if (!file) return;
    setSaving(true);
    setMsg(null);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("code", code.trim() || file.name.replace(/\.docx$/i, ""));
      fd.append("name", name.trim() || file.name);
      fd.append("document_type", docType);
      fd.append("file", file);
      const res = await fetch("/api/v1/templates", {
        method: "POST",
        credentials: "include",
        body: fd,
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        const detail = body?.detail;
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail || res.status));
      }
      setMsg("Шаблон загружен и готов к использованию");
      setOpen(false);
      setCode("");
      setName("");
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить шаблон");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Шаблоны документов"
        subtitle="Word (.docx) → проверка переменных → генерация договоров и протоколов"
        actions={<Button onClick={() => setOpen(true)}>+ Загрузить DOCX</Button>}
      />

      {msg ? (
        <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {msg}
        </div>
      ) : null}

      <div className="mb-4 rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-900">
        <b>Как добавить шаблон:</b> 1) подготовьте Word-файл (например договор) — 2) нажмите{" "}
        <b>«+ Загрузить DOCX»</b> — 3) укажите код и тип. В файле можно использовать переменные вида{" "}
        <code>{"{{counterparty_name}}"}</code>, <code>{"{{contract_number}}"}</code>, <code>{"{{total_amount}}"}</code>.
      </div>

      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading ? (
        <Table
          columns={[
            { key: "c", label: "Код" },
            { key: "n", label: "Название" },
            { key: "t", label: "Тип" },
            { key: "v", label: "Версия" },
            { key: "p", label: "Переменные" },
            { key: "a", label: "Активен" },
          ]}
          rows={items.map((t) => [
            <code key={t.id} className="text-xs">
              {t.code}
            </code>,
            t.name,
            DOC_TYPES.find((d) => d.value === t.document_type)?.label || t.document_type,
            t.version,
            t.placeholders?.slice(0, 8).join(", ") || "—",
            <Badge key="a" tone={t.is_active ? "ok" : "default"}>
              {t.is_active ? "да" : "нет"}
            </Badge>,
          ])}
          empty="Шаблонов пока нет — нажмите «+ Загрузить DOCX»"
        />
      ) : null}

      <Modal open={open} title="Загрузить шаблон DOCX" onClose={() => setOpen(false)}>
        <div className="grid gap-3">
          <Field label="Файл Word (.docx) *">
            <input
              ref={inputRef}
              type="file"
              accept=".docx"
              className="block w-full text-sm"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </Field>
          <Field label="Код * (латиницей, напр. contract-v1)">
            <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="contract-v1" />
          </Field>
          <Field label="Название *">
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Договор на испытания" />
          </Field>
          <Field label="Тип документа">
            <Select value={docType} onChange={(e) => setDocType(e.target.value)}>
              {DOC_TYPES.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Отмена
          </Button>
          <Button onClick={upload} disabled={saving || !file || !name.trim()}>
            {saving ? "Загружаем…" : "Загрузить"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
