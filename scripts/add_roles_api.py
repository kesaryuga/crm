from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\users.py")
t = p.read_text(encoding="utf-8")

# 1) Permission catalog + RoleCreate/Update
if "PERMISSION_CATALOG" not in t:
    catalog = '''

PERMISSION_CATALOG: dict[str, str] = {
    "admin.all": "Полный доступ",
    "crm.view": "Контрагенты — просмотр",
    "crm.edit": "Контрагенты — создание/изменение",
    "tasks.view": "Задачи — просмотр",
    "tasks.create": "Задачи — создание",
    "tasks.edit": "Задачи — изменение",
    "tasks.delegate": "Задачи — делегирование",
    "contracts.view": "Договоры — просмотр",
    "contracts.create": "Договоры — создание",
    "contracts.edit": "Договоры — изменение",
    "works.view": "Испытания — просмотр",
    "works.edit": "Испытания — изменение",
    "protocols.view": "Протоколы — просмотр",
    "protocols.edit": "Протоколы — изменение",
    "equipment.view": "Оборудование — просмотр",
    "equipment.edit": "Оборудование — изменение",
    "services.view": "Услуги — просмотр",
    "documents.generate": "Генерация документов",
    "export": "Экспорт",
    "users.view": "Пользователи — просмотр",
    "users.manage": "Пользователи — управление",
    "audit.view": "Журнал действий",
}

'''
    t = t.replace("class RoleOut(BaseModel):", catalog + "class RoleOut(BaseModel):", 1)

if "class RoleCreate" not in t:
    models = '''

class RoleCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    permissions: list[str] = []


class RoleUpdate(BaseModel):
    name: str | None = None
    permissions: list[str] | None = None

'''
    t = t.replace("class PermissionOut(BaseModel):", "class PermissionOut(BaseModel):", 1)
    t = t.replace("class UserOut(BaseModel):", models + "class UserOut(BaseModel):", 1)

# 2) endpoints after list_roles
if 'router.post("/roles"' not in t:
    endpoints = '''

@router.post("/roles", response_model=RoleOut)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RoleOut:
    _require_admin(user)
    _ensure_base_roles(db)
    code = payload.code.strip().lower().replace(" ", "_")
    exists = db.scalar(select(Role).where(Role.code == code))
    if exists:
        raise HTTPException(
            status_code=409,
            detail={"code": "ROLE_EXISTS", "message": "Роль с таким кодом уже есть"},
        )
    role = Role(code=code, name=payload.name.strip())
    db.add(role)
    db.flush()
    for pcode in payload.permissions:
        perm = db.scalar(select(Permission).where(Permission.code == pcode))
        if not perm:
            perm = Permission(code=pcode, name=PERMISSION_CATALOG.get(pcode, pcode))
            db.add(perm)
            db.flush()
        if perm not in role.permissions:
            role.permissions.append(perm)
    write_audit(db, actor_user_id=user.id, action="create", entity_type="role", entity_id=role.id)
    db.commit()
    db.refresh(role)
    return RoleOut(
        id=role.id,
        code=role.code,
        name=role.name,
        permissions=sorted(p.code for p in role.permissions),
    )


@router.patch("/roles/{rid}", response_model=RoleOut)
def update_role(
    rid: str,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RoleOut:
    _require_admin(user)
    role = db.get(Role, rid)
    if not role:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Роль не найдена"},
        )
    if payload.name is not None:
        role.name = payload.name.strip()
    if payload.permissions is not None:
        role.permissions.clear()
        db.flush()
        for pcode in payload.permissions:
            perm = db.scalar(select(Permission).where(Permission.code == pcode))
            if not perm:
                perm = Permission(code=pcode, name=PERMISSION_CATALOG.get(pcode, pcode))
                db.add(perm)
                db.flush()
            role.permissions.append(perm)
    write_audit(db, actor_user_id=user.id, action="update", entity_type="role", entity_id=role.id)
    db.commit()
    db.refresh(role)
    return RoleOut(
        id=role.id,
        code=role.code,
        name=role.name,
        permissions=sorted(p.code for p in role.permissions),
    )


@router.get("/permissions/catalog")
def permission_catalog(
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    if not user.has("users.manage") and not user.has("admin.all"):
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Нет прав"},
        )
    return PERMISSION_CATALOG

'''
    marker = '@router.get("/permissions", response_model=list[PermissionOut])'
    t = t.replace(marker, endpoints + "\n" + marker, 1)

p.write_text(t, encoding="utf-8")
print("users.py roles API ok")
