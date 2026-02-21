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
    import main
    return main.templates.get_template("login.html").render(request=request)


@router.post("/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Вход пользователя по имени пользователя"""
    # Ищем пользователя
    stmt = select(User).where(User.username == request.username, User.is_active == True)
    user = db.execute(stmt).scalar_one_or_none()
    
    if not user:
        # Если пользователь не найден, создаём нового
        user = User(username=request.username, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Создаём сессию
    session_id = create_session(user.id, user.username)
    
    response = {
        "id": user.id,
        "username": user.username,
        "session_id": session_id
    }
    
    # Устанавливаем cookie
    redirect_response = RedirectResponse(url="/profile", status_code=303)
    redirect_response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=604800,  # 7 дней
        samesite="lax"
    )
    
    return redirect_response


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
    """Проверить наличие API токена у текущего пользователя"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return {"has_token": False}
    
    from .auth import get_session
    session = get_session(session_id)
    if not session:
        return {"has_token": False}
    
    # Проверяем токен
    token = get_user_api_token(db, session["user_id"])
    
    if token:
        # Получаем ID токена для редактирования
        stmt = select(UserApiToken).where(
            UserApiToken.user_id == session["user_id"],
            UserApiToken.is_active == True
        ).limit(1)
        user_token = db.execute(stmt).scalar_one_or_none()
        
        return {
            "has_token": True,
            "token_id": user_token.id if user_token else None
        }
    
    return {"has_token": False}


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Страница профиля пользователя"""
    import main
    
    # Проверяем аутентификацию
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/login", status_code=303)
    
    from .auth import get_session
    session = get_session(session_id)
    if not session:
        return RedirectResponse(url="/login", status_code=303)
    
    return main.templates.get_template("profile.html").render(request=request)
