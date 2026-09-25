from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\crm.py")
t = p.read_text(encoding="utf-8")
old = 'raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Объект не найден"})'
new = (
    "raise HTTPException(\n"
    "            status_code=404,\n"
    '            detail={"code": "NOT_FOUND", "message": "Объект не найден"},\n'
    "        )"
)
if old in t:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("fixed")
else:
    print("not found")
