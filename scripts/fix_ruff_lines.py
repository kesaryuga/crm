from pathlib import Path

# fix long lines
base = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api")
for name in ("tasks.py", "users.py"):
    p = base / name
    t = p.read_text(encoding="utf-8")
    t = t.replace(
        '    if not user.has("tasks.delegate") and not user.has("admin.all") and row.creator_user_id != user.id:',
        "    allowed = user.has(\"tasks.delegate\") or user.has(\"admin.all\")\n"
        "    if not allowed and row.creator_user_id != user.id:",
    )
    t = t.replace(
        '        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Нет прав на управление пользователями"})',
        "        raise HTTPException(\n"
        "            status_code=403,\n"
        "            detail={\"code\": \"FORBIDDEN\", \"message\": \"Нет прав на управление пользователями\"},\n"
        "        )",
    )
    t = t.replace(
        '        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Нет прав на просмотр пользователей"})',
        "        raise HTTPException(\n"
        "            status_code=403,\n"
        "            detail={\"code\": \"FORBIDDEN\", \"message\": \"Нет прав на просмотр пользователей\"},\n"
        "        )",
    )
    p.write_text(t, encoding="utf-8")
    print("fixed", name)
