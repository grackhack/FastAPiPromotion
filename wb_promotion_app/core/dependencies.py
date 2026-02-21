"""
Зависимости FastAPI
Аутентификация, получение пользователя, WB клиент
"""
from typing import Optional
from fastapi import Request, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..config import get_db
from ..models import User, UserApiToken
from ..auth import get_current_user_from_session, get_session, delete_session, get_user_api_token
from ..services.wb_service import WBService


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Получить текущего пользователя из session cookie.
    Возвращает None если не авторизован.
    """
    return await get_current_user_from_session(request)


async def require_auth(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Требует авторизации.
    Перенаправляет на /login если не авторизован.
    """
    user = await get_current_user_from_session(request)
    
    if not user:
        # Для API запросов возвращаем 401
        if request.url.path.startswith('/api/'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Требуется авторизация"
            )
        # Для веб-страниц - редирект
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    
    return user


async def require_token(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
) -> str:
    """
    Требует наличия WB API токена у пользователя.
    Возвращает токен.
    """
    stmt = select(UserApiToken).where(
        UserApiToken.user_id == user.id,
        UserApiToken.is_active == True
    ).limit(1)
    
    token_record = db.execute(stmt).scalar_one_or_none()
    
    if not token_record:
        # Для API запросов возвращаем 403
        if request.url.path.startswith('/api/'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Необходимо добавить WB API токен в личном кабинете"
            )
        # Для веб-страниц - редирект на профиль
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/profile"}
        )
    
    return token_record.token


def get_wb_client(
    token: str = Depends(require_token)
):
    """
    Создать WB API сервис для текущего пользователя.
    Возвращает None если токен не найден.
    """
    from ..services.wb_service import WBService
    from ..api_client import WBPromotionClient
    
    if not token:
        return None

    client = WBPromotionClient(token)
    return WBService(client)


async def get_wb_client_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[WBService]:
    """
    Создать WB API сервис для текущего пользователя (опционально).
    Возвращает None если пользователь не авторизован или нет токена.
    """
    from ..services.wb_service import WBService
    from ..api_client import WBPromotionClient
    
    user = await get_current_user_from_session(request)
    if not user:
        return None
    
    token = get_user_api_token(db, user.id)
    if not token:
        return None

    client = WBPromotionClient(token)
    return WBService(client)
