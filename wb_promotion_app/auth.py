"""
Веб-аутентификация пользователей через session cookies
"""
from typing import Optional
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select
import secrets
from datetime import datetime, timedelta

from .models import User, UserApiToken
from .config import SessionLocal


# Хранилище сессий (в памяти для простоты)
# В продакшене лучше использовать Redis или базу данных
sessions: dict[str, dict] = {}


def create_session(user_id: int, username: str) -> str:
    """Создать новую сессию для пользователя"""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "user_id": user_id,
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(days=7)
    }
    return session_id


def create_session_with_token(user_id: int, username: str, api_token: Optional[str]) -> str:
    """Создать новую сессию для пользователя с API токеном"""
    session_id = secrets.token_urlsafe(32)
    session_data = {
        "user_id": user_id,
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(days=7)
    }
    # Сохраняем токен в сессию если он есть
    if api_token:
        session_data['api_token'] = api_token
    sessions[session_id] = session_data
    return session_id


def get_session(session_id: str) -> Optional[dict]:
    """Получить данные сессии"""
    session = sessions.get(session_id)
    if session and session["expires_at"] > datetime.now():
        return session
    elif session:
        # Сессия истекла
        sessions.pop(session_id, None)
    return None


def delete_session(session_id: str):
    """Удалить сессию"""
    sessions.pop(session_id, None)


def cleanup_expired_sessions():
    """Очистить истёкшие сессии"""
    now = datetime.now()
    expired = [sid for sid, s in sessions.items() if s["expires_at"] < now]
    for sid in expired:
        sessions.pop(sid, None)


async def get_current_user_from_session(request: Request) -> Optional[User]:
    """Получить текущего пользователя из session cookie"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None

    session = get_session(session_id)
    if not session:
        return None

    # Проверка в БД что пользователь всё ещё активен
    db = SessionLocal()
    try:
        stmt = select(User).where(User.id == session["user_id"], User.is_active == True)
        user = db.execute(stmt).scalar_one_or_none()
        if not user:
            delete_session(session_id)
            return None
        return user
    finally:
        db.close()


async def require_auth(request: Request) -> User:
    """Требует аутентификации"""
    user = await get_current_user_from_session(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    return user


async def get_current_user_optional(request: Request) -> Optional[dict]:
    """Опциональная аутентификация"""
    return await get_current_user_from_session(request)


def get_user_api_token(db: Session, user_id: int) -> Optional[str]:
    """Получить активный API токен пользователя"""
    stmt = select(UserApiToken).where(
        UserApiToken.user_id == user_id,
        UserApiToken.is_active == True
    ).limit(1)
    token = db.execute(stmt).scalar_one_or_none()
    return token.token if token else None
