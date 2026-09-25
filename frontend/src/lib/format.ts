export function fmtDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function fmtDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function fmtMoney(value: string | number | null | undefined, currency = "BYN"): string {
  if (value === null || value === undefined || value === "") return "—";
  const n = typeof value === "string" ? Number(value) : value;
  if (Number.isNaN(n)) return String(value);
  return `${n.toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`;
}

export function toDateInput(value: string | null | undefined): string {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toISOString().slice(0, 10);
}

export const TASK_TYPES: Record<string, string> = {
  call: "Звонок",
  meeting: "Встреча",
  document_prepare: "Подготовка документа",
  document_send: "Отправка документа",
  testing: "Испытание",
  payment_check: "Проверка оплаты",
  other: "Другое",
};

export const TASK_STATUSES: Record<string, string> = {
  new: "Новая",
  in_progress: "В работе",
  done: "Выполнена",
  cancelled: "Отменена",
};

export const CONTRACT_STATUSES: Record<string, string> = {
  draft: "Черновик",
  approval: "Согласование",
  signing: "Подписание",
  active: "Действует",
  completed: "Выполнен",
  terminated: "Расторгнут",
  archived: "Архив",
};

export const WORK_STATUSES: Record<string, string> = {
  planned: "Запланировано",
  assigned: "Назначено",
  in_progress: "Выполняется",
  results_entered: "Результаты внесены",
  protocol_ready: "Протокол сформирован",
  done: "Завершено",
};

export const PRIORITIES: Record<string, string> = {
  low: "Низкий",
  medium: "Средний",
  high: "Высокий",
  urgent: "Срочный",
};

export const CP_STATUSES: Record<string, string> = {
  active: "Активный",
  lead: "Лид",
  inactive: "Неактивный",
  archived: "Архив",
};
