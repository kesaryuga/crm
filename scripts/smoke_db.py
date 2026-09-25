import os
import sys

sys.path.insert(0, r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend")

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres.chbmuoyuscghinfxywbs:"
    "uB1pnoArMMEea8BF1MkV-WbKXvmn5YRb@"
    "aws-1-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"
)
os.environ["SECRET_KEY"] = "1KClmHzpSbjambMc_KGlYn_C1hjTt4wFwy-OvJwlc4g84PDu50iRJSOyW2MHGNh1"
os.environ["ADMIN_EMAIL"] = "admin@kit-lab.by"
os.environ["ADMIN_PASSWORD"] = "2W1X7eAWOQovF0U7D_U-q3Cg"
os.environ["APP_ENV"] = "staging"

from app.core.db import Base, get_engine  # noqa: E402
from app.api.auth import bootstrap_admin  # noqa: E402
from app.core.db import get_sessionmaker  # noqa: E402

engine = get_engine()
Base.metadata.create_all(bind=engine)
print("schema ok")

db = get_sessionmaker()()
try:
    user = bootstrap_admin(db)
    print("admin", user.email if user else None)
finally:
    db.close()
print("READY")
