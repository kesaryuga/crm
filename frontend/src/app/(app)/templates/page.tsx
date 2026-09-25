"use client";

import { useEffect, useState } from "react";
import {
  Badge,
  Button,
  ErrorBox,
  PageHeader,
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

export default function TemplatesPage() {
  const [items, setItems] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
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

  return (
    <div>
      <PageHeader
        title="Шаблоны документов"
        subtitle="DOCX: загрузка → проверка переменных → активация"
        actions={
          <Button
            variant="secondary"
            onClick={() =>
              alert(
                "Загрузка DOCX: POST /api/v1/templates (multipart: code, name, document_type, file).\nЧерез интерфейс — следующий шаг, API уже готов.",
              )
            }
          >
            Как загрузить
          </Button>
        }
      />
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
            t.code,
            t.name,
            t.document_type,
            t.version,
            t.placeholders?.slice(0, 6).join(", ") || "—",
            <Badge key="a" tone={t.is_active ? "ok" : "default"}>
              {t.is_active ? "да" : "нет"}
            </Badge>,
          ])}
          empty="Шаблонов нет. Загрузите DOCX через API или следующий релиз UI."
        />
      ) : null}
    </div>
  );
}
