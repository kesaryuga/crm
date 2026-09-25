from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\main.py")
t = p.read_text(encoding="utf-8")
t = t.replace(
    "from app.core.db import Base, get_engine, get_sessionmaker",
    "from app.core.db import Base, get_engine, get_sessionmaker\nfrom app.core.middleware import LoginRateLimitMiddleware, SecurityHeadersMiddleware",
)
t = t.replace(
    "from app.core.middleware import LoginRateLimitMiddleware, SecurityHeadersMiddleware\n\n\n@asynccontextmanager",
    "\n\n@asynccontextmanager",
)
# remove duplicate import line after helper
t = t.replace(
    "    except Exception:\n        pass\n\n\nfrom app.core.middleware import LoginRateLimitMiddleware, SecurityHeadersMiddleware\n",
    "    except Exception:\n        pass\n",
)
p.write_text(t, encoding="utf-8")
print("ok")
