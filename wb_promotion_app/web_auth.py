"""
Веб-роуты для аутентификации пользователей
"""
from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from .config import get_db
from .models import User, UserApiToken
from .auth import create_session, delete_session, get_current_user_from_session, get_user_api_token
from .schemas import UserCreate, UserApiTokenCreate


router = APIRouter(tags=["Web Auth"])


class LoginRequest(BaseModel):
    username: str


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    from . import main
    return main.templates.get_template("login.html").render(request=request)


@router.post("/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Вход пользователя по имени пользователя"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Ищем пользователя
        stmt = select(User).where(User.username == request.username, User.is_active == True)
        user = db.execute(stmt).scalar_one_or_none()

        if not user:
            # Если пользователь не найден, создаём нового
            logger.info(f"Создание нового пользователя: {request.username}")
            user = User(username=request.username, is_active=True)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Пользователь создан с ID: {user.id}")

        # Создаём сессию
        session_id = create_session(user.id, user.username)
        logger.info(f"Сессия создана для пользователя {user.id}: {session_id[:8]}...")

        # Проверяем наличие токена и сохраняем в сессию
        token = get_user_api_token(db, user.id)
        if token:
            # Сохраняем токен в сессию для быстрого доступа
            from . import auth
            session_data = auth.get_session(session_id)
            if session_data:
                session_data['api_token'] = token
                logger.info(f"API токен сохранён в сессию для {user.username}")

        # Устанавливаем cookie
        redirect_response = RedirectResponse(url="/", status_code=303)  # Редирект на страницу кампаний
        redirect_response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=604800,  # 7 дней
            samesite="lax"
        )

        logger.info(f"Вход выполнен успешно для {user.username}, редирект на /")
        return redirect_response
    except Exception as e:
        logger.exception(f"Ошибка входа для {request.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка входа: {str(e)}"
        )


@router.get("/logout")
async def logout(request: Request):
    """Выход пользователя"""
    session_id = request.cookies.get("session_id")
    if session_id:
        delete_session(session_id)
    
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session_id")
    return response


@router.get("/auth/me")
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Получить текущего пользователя"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    from .auth import get_session
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Сессия истекла")
    
    # Получаем пользователя из БД
    stmt = select(User).where(User.id == session["user_id"], User.is_active == True)
    user = db.execute(stmt).scalar_one_or_none()
    
    if not user:
        delete_session(session_id)
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.get("/auth/token")
async def get_current_token(request: Request, db: Session = Depends(get_db)):
    """Проверить наличие API токена у текущего пользователя и вернуть его"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return {"has_token": False}

    from .auth import get_session
    session = get_session(session_id)
    if not session:
        return {"has_token": False}

    # Сначала пробуем получить токен из сессии (быстрый путь)
    if 'api_token' in session:
        return {
            "has_token": True,
            "token": session['api_token']
        }

    # Проверяем токен в БД
    token = get_user_api_token(db, session["user_id"])

    if token:
        # Сохраняем в сессию для будущих запросов
        session['api_token'] = token
        
        # Получаем ID токена для редактирования
        stmt = select(UserApiToken).where(
            UserApiToken.user_id == session["user_id"],
            UserApiToken.is_active == True
        ).limit(1)
        user_token = db.execute(stmt).scalar_one_or_none()

        return {
            "has_token": True,
            "token_id": user_token.id if user_token else None,
            "token": token  # Возвращаем сам токен для использования в API
        }

    return {"has_token": False}


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Страница профиля пользователя"""
    from . import main
    
    # Проверяем аутентификацию
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/login", status_code=303)
    
    from .auth import get_session
    session = get_session(session_id)
    if not session:
        return RedirectResponse(url="/login", status_code=303)
    
    return main.templates.get_template("profile.html").render(request=request)
