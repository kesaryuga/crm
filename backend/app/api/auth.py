from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import (
    create_session_token,
    hash_password,
    parse_session_token,
    verify_password,
)
from app.models import Permission, Role, User
from app.services import write_audit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

COOKIE = Cookie(default=None, alias="crm_session")


class LoginIn(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class UserOut(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    role: str | None = None
    permissions: list[str] = []


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        role=user.role.code if user.role else None,
        permissions=sorted(user.permission_codes),
    )


def get_current_user(
    db: Session = Depends(get_db),
    crm_session: str | None = COOKIE,
) -> User:
    if not crm_session:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Нет сессии"},
        )
    user_id = parse_session_token(crm_session)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Сессия недействительна"},
        )
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Пользователь недоступен"},
        )
    return user


def require_permission(code: str):
    def _dep(user: User = Depends(get_current_user)) -> User:
        if not user.has(code):
            raise HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN", "message": f"Нет права: {code}"},
            )
        return user

    return _dep


@router.post("/login", response_model=UserOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)) -> UserOut:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(user.password_hash, payload.password):
        write_audit(
            db,
            actor_user_id=user.id if user else None,
            action="login_failed",
            entity_type="user",
            entity_id=user.id if user else None,
        )
        db.commit()
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_CREDENTIALS", "message": "Неверный email или пароль"},
        )
    if not user.is_active:
        write_audit(
            db,
            actor_user_id=user.id,
            action="login_blocked",
            entity_type="user",
            entity_id=user.id,
        )
        db.commit()
        raise HTTPException(
            status_code=403,
            detail={"code": "USER_DISABLED", "message": "Учётная запись заблокирована"},
        )

    user.last_login_at = datetime.now(UTC)
    write_audit(db, actor_user_id=user.id, action="login", entity_type="user", entity_id=user.id)
    db.commit()
    db.refresh(user)

    settings = get_settings()
    secure = settings.app_env == "production" or settings.app_url.startswith("https")
    response.set_cookie(
        key=settings.session_cookie_name,
        value=create_session_token(user.id),
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=60 * 60 * 12,
    )
    return _user_out(user)


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    crm_session: str | None = COOKIE,
) -> dict[str, str]:
    user_id = parse_session_token(crm_session) if crm_session else None
    if user_id:
        write_audit(
            db,
            actor_user_id=user_id,
            action="logout",
            entity_type="user",
            entity_id=user_id,
        )
        db.commit()
    response.delete_cookie(get_settings().session_cookie_name)
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(user)


def bootstrap_admin(db: Session) -> User | None:
    settings = get_settings()
    email = settings.admin_email
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        return existing

    role = db.scalar(select(Role).where(Role.code == "admin"))
    if not role:
        role = Role(code="admin", name="Администратор")
        db.add(role)
        db.flush()

    admin_perm = db.scalar(select(Permission).where(Permission.code == "admin.all"))
    if not admin_perm:
        admin_perm = Permission(code="admin.all", name="Полный доступ")
        db.add(admin_perm)
        db.flush()
    if admin_perm not in role.permissions:
        role.permissions.append(admin_perm)

    user = User(
        email=email,
        password_hash=hash_password(settings.admin_password),
        first_name="Админ",
        last_name="КИТ-лаб",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    write_audit(
        db,
        actor_user_id=None,
        action="bootstrap_admin",
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()
    return user
