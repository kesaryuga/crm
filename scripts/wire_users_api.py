from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\users.py")
t = p.read_text(encoding="utf-8")
t = t.replace("from pydantic import BaseModel, EmailStr, Field", "from pydantic import BaseModel, Field, field_validator")
t = t.replace("email: EmailStr", "email: str")
t = t.replace("email: EmailStr | None = None", "email: str | None = None")
# add validator after class UserCreate start
old = """class UserCreate(BaseModel):
    email: str"""
new = """class UserCreate(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def _email_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Некорректный email")
        return v
"""
if old in t and "@field_validator" not in t:
    t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("users.py patched")

init = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\__init__.py")
it = init.read_text(encoding="utf-8")
if "users_router" not in it:
    it = it.replace(
        "from app.api.works import router as works_router",
        "from app.api.users import router as users_router\nfrom app.api.works import router as works_router",
    )
    it = it.replace('    "works_router",', '    "users_router",\n    "works_router",')
    init.write_text(it, encoding="utf-8")
    print("api/__init__ patched")

main = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\main.py")
mt = main.read_text(encoding="utf-8")
if "users_router" not in mt:
    mt = mt.replace(
        "from app.api.works import router as works_router",
        "from app.api.users import router as users_router\nfrom app.api.works import router as works_router",
    )
    mt = mt.replace("    app.include_router(io_router)", "    app.include_router(io_router)\n    app.include_router(users_router)")
    main.write_text(mt, encoding="utf-8")
    print("main.py patched")
print("done")
