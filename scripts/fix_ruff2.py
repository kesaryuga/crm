from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\users.py")
t = p.read_text(encoding="utf-8")
t = t.replace(
    'raise HTTPException(status_code=409, detail={"code": "USER_EXISTS", "message": "Пользователь уже существует"})',
    "raise HTTPException(\n"
    "            status_code=409,\n"
    "            detail={\"code\": \"USER_EXISTS\", \"message\": \"Пользователь уже существует\"},\n"
    "        )",
)
t = t.replace(
    'raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Пользователь не найден"})',
    "raise HTTPException(\n"
    "            status_code=404,\n"
    "            detail={\"code\": \"NOT_FOUND\", \"message\": \"Пользователь не найден\"},\n"
    "        )",
)
p.write_text(t, encoding="utf-8")
print("ok")
