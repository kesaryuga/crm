import os
import sys

sys.path.insert(0, r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend")

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres.chbmuoyuscghinfxywbs:"
    "uB1pnoArMMEea8BF1MkV-WbKXvmn5YRb@"
    "aws-1-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"
)
os.environ.setdefault("SECRET_KEY", "1KClmHzpSbjambMc_KGlYn_C1hjTt4wFwy-OvJwlc4g84PDu50iRJSOyW2MHGNh1")

from sqlalchemy import select  # noqa: E402

from app.api.users import _ensure_base_roles  # noqa: E402
from app.core.db import get_sessionmaker  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import Role, User  # noqa: E402

USERS = [
    {
        "email": "boss@kit-lab.by",
        "password": "boss2026",
        "first_name": "Иван",
        "last_name": "Петров",
        "role": "boss",
    },
    {
        "email": "manager@kit-lab.by",
        "password": "manager2026",
        "first_name": "Анна",
        "last_name": "Сидорова",
        "role": "manager",
    },
    {
        "email": "engineer@kit-lab.by",
        "password": "engineer2026",
        "first_name": "Пётр",
        "last_name": "Иванов",
        "role": "engineer",
    },
]

db = get_sessionmaker()()
try:
    _ensure_base_roles(db)
    for spec in USERS:
        role = db.scalar(select(Role).where(Role.code == spec["role"]))
        user = db.scalar(select(User).where(User.email == spec["email"]))
        if not user:
            user = User(
                email=spec["email"],
                password_hash=hash_password(spec["password"]),
                first_name=spec["first_name"],
                last_name=spec["last_name"],
                role_id=role.id if role else None,
                is_active=True,
            )
            db.add(user)
            print("created", spec["email"], spec["role"])
        else:
            user.password_hash = hash_password(spec["password"])
            user.role_id = role.id if role else user.role_id
            user.is_active = True
            print("updated", spec["email"], spec["role"])
    db.commit()
    print("OK")
finally:
    db.close()
