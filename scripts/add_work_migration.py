from pathlib import Path

# Add ALTER TABLE for new work columns on startup (create_all won't add columns)
p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\main.py")
t = p.read_text(encoding="utf-8")
if "_ensure_work_columns" not in t:
    t = t.replace(
        "from app.core.db import Base, get_engine, get_sessionmaker",
        "from app.core.db import Base, get_engine, get_sessionmaker",
    )
    helper = '''

def _ensure_work_columns() -> None:
    """create_all не добавляет колонки в существующие таблицы — мигрируем мягко."""
    engine = get_engine()
    cols = {
        "test_type": "VARCHAR(64) DEFAULT ''",
        "address": "VARCHAR(500) DEFAULT ''",
        "parameters_count": "INTEGER DEFAULT 0",
        "sample_count": "INTEGER DEFAULT 0",
        "method": "VARCHAR(255) DEFAULT ''",
        "contact_person": "VARCHAR(255) DEFAULT ''",
        "contact_phone": "VARCHAR(64) DEFAULT ''",
    }
    try:
        with engine.begin() as conn:
            existing = {
                row[0]
                for row in conn.exec_driver_sql(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'works'"
                )
            }
            for name, ddl in cols.items():
                if name not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE works ADD COLUMN IF NOT EXISTS {name} {ddl}")
    except Exception:
        pass

'''
    t = t.replace("from app.core.middleware import", helper + "\nfrom app.core.middleware import", 1)
    t = t.replace(
        "    Base.metadata.create_all(bind=get_engine())",
        "    Base.metadata.create_all(bind=get_engine())\n    _ensure_work_columns()",
    )
p.write_text(t, encoding="utf-8")
print("main.py migration ok")
