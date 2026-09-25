import sys

import psycopg

url = (
    "postgresql://postgres.chbmuoyuscghinfxywbs:"
    "uB1pnoArMMEea8BF1MkV-WbKXvmn5YRb@"
    "aws-1-eu-west-1.pooler.supabase.com:5432/postgres"
)

try:
    with psycopg.connect(url, connect_timeout=20, sslmode="require") as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user")
            print("OK", cur.fetchone())
            cur.execute("SELECT version()")
            print(cur.fetchone()[0][:80])
except Exception as exc:
    print("FAIL", type(exc).__name__, str(exc)[:300])
    sys.exit(1)
