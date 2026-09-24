from __future__ import annotations

import csv
import io
from typing import Any

CP_COLUMNS = {
    "full_name": "Наименование",
    "short_name": "Краткое",
    "unp": "УНП",
    "phone": "Телефон",
    "email": "Email",
    "legal_address": "Юр. адрес",
    "notes": "Заметки",
}
REQUIRED = ("full_name",)


def parse_counterparties_csv(data: bytes) -> list[dict[str, str]]:
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict[str, str]] = []
    for raw in reader:
        item = {k: (raw.get(k) or "").strip() for k in CP_COLUMNS}
        if not any(item.values()):
            continue
        rows.append(item)
    return rows


def counterparties_to_csv(rows: list[Any]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(CP_COLUMNS.keys())
    for r in rows:
        writer.writerow([getattr(r, k, "") for k in CP_COLUMNS])
    return buf.getvalue()


def tasks_to_csv(rows: list[Any]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(
        [
            "title",
            "description",
            "task_type",
            "priority",
            "status",
            "due_at",
            "completed_at",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.title,
                r.description,
                r.task_type,
                r.priority,
                r.status,
                r.due_at.isoformat() if r.due_at else "",
                r.completed_at.isoformat() if r.completed_at else "",
            ]
        )
    return buf.getvalue()


def contracts_to_csv(rows: list[Any]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(
        [
            "number",
            "number_year",
            "contract_date",
            "status",
            "currency",
            "subtotal",
            "vat_amount",
            "total_amount",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.number,
                r.number_year or "",
                r.contract_date.date().isoformat() if r.contract_date else "",
                r.status,
                r.currency,
                str(r.subtotal),
                str(r.vat_amount),
                str(r.total_amount),
            ]
        )
    return buf.getvalue()


def counterparties_to_xlsx(rows: list[Any]) -> bytes:
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RuntimeError("openpyxl не установлен") from exc
    wb = Workbook()
    ws = wb.active
    ws.title = "Контрагенты"
    ws.append(list(CP_COLUMNS.keys()))
    for r in rows:
        ws.append([str(getattr(r, k, "") or "") for k in CP_COLUMNS])
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()
