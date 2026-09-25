from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\tests\test_hardening.py")
t = p.read_text(encoding="utf-8")
old = """def test_login_rate_limit() -> None:
    for _ in range(10):
        assert check_login_rate("ip-test") is True
    assert check_login_rate("ip-test") is False
    assert check_login_rate("ip-other") is True"""
new = """def test_login_rate_limit() -> None:
    from app.core.middleware import _LOGIN_LIMIT

    for _ in range(_LOGIN_LIMIT):
        assert check_login_rate("ip-test") is True
    assert check_login_rate("ip-test") is False
    assert check_login_rate("ip-other") is True"""
if old not in t:
    raise SystemExit("pattern not found")
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("ok")
