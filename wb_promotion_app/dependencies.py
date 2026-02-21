"""
Зависимости для аутентификации и работы с пользователями
"""
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import select

from .config import get_db
from .models import User, UserApiToken


class TokenNotFoundError(Exception):
    """Ошибка когда токен не найден"""
    pass


class TokenNotActiveError(Exception):
    """Ошибка когда токен не активен"""
    pass


class UserNotFoundError(Exception):
    """Ошибка когда пользователь не найден"""
    pass


class UserNotActiveError(Exception):
    """Ошибка когда пользователь не активен"""
    pass


def get_token_from_header(
    x_api_token: Annotated[
        Optional[str],
        Header(
            alias="X-API-Token",
            description="WB API токен пользователя для аутентификации"
        )
    ] = None
) -> Optional[str]:
    """
    Получить токен из заголовка X-API-Token
    """
    return x_api_token


def get_current_user_by_token(
    token: Annotated[Optional[str], Depends(get_token_from_header)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    """
    Получить текущего пользователя по токену.
    
    Ищет активный токен в БД и возвращает связанного с ним активного пользователя.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходимо предоставить заголовок X-API-Token"
        )
    
    # Ищем активный токен
    stmt = select(UserApiToken).where(
        UserApiToken.token == token,
        UserApiToken.is_active == True
    )
    user_token = db.execute(stmt).scalar_one_or_none()
    
    if not user_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или неактивный токен"
        )
    
    # Проверяем активность пользователя
    if not user_token.user or not user_token.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не активен"
        )
    
    return user_token.user


def get_current_user_optional(
    token: Annotated[Optional[str], Depends(get_token_from_header)],
    db: Annotated[Session, Depends(get_db)]
) -> Optional[User]:
    """
    Получить текущего пользователя по токену (опционально).
    
    Возвращает None если токен не предоставлен или не найден.
    """
    if not token:
        return None
    
    try:
        return get_current_user_by_token(token, db)
    except HTTPException:
        return None


# Типы для аннотаций в эндпоинтах
CurrentUser = Annotated[User, Depends(get_current_user_by_token)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]
DbSession = Annotated[Session, Depends(get_db)]
