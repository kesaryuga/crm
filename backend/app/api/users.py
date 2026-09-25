from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.db import get_db
from app.core.security import hash_password
from app.models import Permission, Role, User
from app.services import write_audit

router = APIRouter(prefix="/api/v1", tags=["users"])




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

class RoleOut(BaseModel):
    id: str
    code: str
    name: str
    permissions: list[str] = []


class PermissionOut(BaseModel):
    code: str
    name: str




class RoleCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    permissions: list[str] = []


class RoleUpdate(BaseModel):
    name: str | None = None
    permissions: list[str] | None = None

class UserOut(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    role_id: str | None = None
    role_code: str | None = None
    role_name: str | None = None
    permissions: list[str] = []
    last_login_at: datetime | None = None
    created_at: datetime | None = None


class UserCreate(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def _email_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Некорректный email")
        return v

    password: str = Field(min_length=6)
    first_name: str = ""
    last_name: str = ""
    role_id: str | None = None
    is_active: bool = True


class UserUpdate(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    role_id: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6)


DEFAULT_ROLES = [
    ("admin", "Администратор", ["admin.all"]),
    ("boss", "Руководитель", [
        "crm.view", "crm.edit", "tasks.view", "tasks.create", "tasks.edit", "tasks.delegate",
        "contracts.view", "contracts.create", "contracts.edit", "works.view", "works.edit",
        "protocols.view", "protocols.edit", "equipment.view", "services.view", "documents.generate",
        "export", "users.view", "users.manage", "audit.view",
    ]),
    ("manager", "Менеджер", [
        "crm.view", "crm.edit", "tasks.view", "tasks.create", "tasks.edit", "tasks.delegate",
        "contracts.view", "contracts.create", "contracts.edit", "works.view", "works.edit",
        "protocols.view", "equipment.view", "services.view", "documents.generate", "export",
    ]),
    ("engineer", "Инженер", [
        "crm.view", "tasks.view", "tasks.create", "tasks.edit", "works.view", "works.edit",
        "protocols.view", "protocols.edit", "equipment.view", "equipment.edit",
        "services.view", "documents.generate",
    ]),
]


def _ensure_base_roles(db: Session) -> None:
    for code, name, perm_codes in DEFAULT_ROLES:
        role = db.scalar(select(Role).where(Role.code == code))
        if not role:
            role = Role(code=code, name=name)
            db.add(role)
            db.flush()
        for pcode in perm_codes:
            perm = db.scalar(select(Permission).where(Permission.code == pcode))
            if not perm:
                perm = Permission(code=pcode, name=pcode.replace(".", " ").title())
                db.add(perm)
                db.flush()
            if perm not in role.permissions:
                role.permissions.append(perm)
    db.commit()


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        role_id=user.role_id,
        role_code=user.role.code if user.role else None,
        role_name=user.role.name if user.role else None,
        permissions=sorted(user.permission_codes),
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


def _require_admin(user: User) -> None:
    if not user.has("users.manage") and not user.has("admin.all"):
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Нет прав на управление пользователями"},
        )


@router.get("/roles", response_model=list[RoleOut])
def list_roles(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[RoleOut]:
    _ensure_base_roles(db)
    rows = db.scalars(select(Role).order_by(Role.name)).all()
    return [
        RoleOut(
            id=r.id,
            code=r.code,
            name=r.name,
            permissions=sorted(p.code for p in r.permissions),
        )
        for r in rows
    ]




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


@router.get("/permissions", response_model=list[PermissionOut])
def list_permissions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[PermissionOut]:
    _require_admin(user)
    rows = db.scalars(select(Permission).order_by(Permission.code)).all()
    return [PermissionOut(code=p.code, name=p.name) for p in rows]


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[UserOut]:
    if not user.has("users.view") and not user.has("users.manage") and not user.has("admin.all"):
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Нет прав на просмотр пользователей"},
        )
    _ensure_base_roles(db)
    rows = db.scalars(select(User).order_by(User.last_name, User.email)).all()
    return [_user_out(u) for u in rows]


@router.post("/users", response_model=UserOut)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserOut:
    _require_admin(user)
    _ensure_base_roles(db)
    exists = db.scalar(select(User).where(User.email == payload.email))
    if exists:
        raise HTTPException(
            status_code=409,
            detail={"code": "USER_EXISTS", "message": "Пользователь уже существует"},
        )
    row = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role_id=payload.role_id,
        is_active=payload.is_active,
    )
    db.add(row)
    write_audit(db, actor_user_id=user.id, action="create", entity_type="user", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return _user_out(row)


@router.get("/users/{uid}", response_model=UserOut)
def get_user(
    uid: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserOut:
    if not user.has("users.view") and not user.has("users.manage") and not user.has("admin.all"):
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Нет прав"})
    row = db.get(User, uid)
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Пользователь не найден"},
        )
    return _user_out(row)


@router.patch("/users/{uid}", response_model=UserOut)
def update_user(
    uid: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserOut:
    _require_admin(user)
    row = db.get(User, uid)
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Пользователь не найден"},
        )
    data = payload.model_dump(exclude_unset=True, exclude={"password"})
    for key, value in data.items():
        setattr(row, key, value)
    if payload.password:
        row.password_hash = hash_password(payload.password)
    write_audit(db, actor_user_id=user.id, action="update", entity_type="user", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return _user_out(row)
