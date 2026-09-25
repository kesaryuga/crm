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

from app.core.db import get_sessionmaker  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import User  # noqa: E402

NEW_PASSWORD = os.environ.get("NEW_ADMIN_PASSWORD", "kitlab2026")

db = get_sessionmaker()()
try:
    user = db.scalar(select(User).where(User.email == "admin@kit-lab.by"))
    if not user:
        print("NO_USER")
        sys.exit(1)
    user.password_hash = hash_password(NEW_PASSWORD)
    db.commit()
    print("OK password updated")
finally:
    db.close()
