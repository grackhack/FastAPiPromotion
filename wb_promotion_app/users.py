"""
Эндпоинты для управления пользователями и их API токенами
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from .config import get_db
from .models import User, UserApiToken
from .schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserWithTokensResponse,
    UserApiTokenCreate,
    UserApiTokenUpdate,
    UserApiTokenResponse,
    UserApiTokenFullResponse,
)
from .dependencies import DbSession, CurrentUser


router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, db: DbSession):
    """
    Создать нового пользователя
    """
    # Проверка на существующего пользователя
    stmt = select(User).where(User.username == user_data.username)
    existing_user = db.execute(stmt).scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует"
        )
    
    # Проверка email если указан
    if user_data.email:
        stmt = select(User).where(User.email == user_data.email)
        existing_email = db.execute(stmt).scalar_one_or_none()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже зарегистрирован"
            )
    
    # Создание пользователя
    user = User(
        username=user_data.username,
        email=user_data.email,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.get("", response_model=List[UserResponse])
def get_users(db: DbSession):
    """
    Получить список всех пользователей
    """
    stmt = select(User).order_by(User.created_at.desc())
    users = db.execute(stmt).scalars().all()
    return users


@router.get("/{user_id}", response_model=UserWithTokensResponse)
def get_user(user_id: int, db: DbSession):
    """
    Получить пользователя по ID с его токенами
    """
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserUpdate, db: DbSession):
    """
    Обновить данные пользователя
    """
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Обновление полей
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: DbSession):
    """
    Удалить пользователя (каскадно удалит все его токены)
    """
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    db.delete(user)
    db.commit()
    
    return None


# ==================== Эндпоинты для токенов ====================

@router.post("/{user_id}/tokens", response_model=UserApiTokenFullResponse, status_code=status.HTTP_201_CREATED)
def create_token(user_id: int, token_data: UserApiTokenCreate, db: DbSession):
    """
    Создать новый API токен для пользователя
    """
    # Проверка существования пользователя
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Создание токена
    token = UserApiToken(
        user_id=user_id,
        token=token_data.token,
        description=token_data.description,
        is_active=True
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    
    return token


@router.get("/{user_id}/tokens", response_model=List[UserApiTokenResponse])
def get_user_tokens(user_id: int, db: DbSession):
    """
    Получить все токены пользователя
    """
    # Проверка существования пользователя
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    stmt = select(UserApiToken).where(
        UserApiToken.user_id == user_id
    ).order_by(UserApiToken.created_at.desc())
    tokens = db.execute(stmt).scalars().all()
    
    return tokens


@router.get("/{user_id}/tokens/{token_id}", response_model=UserApiTokenResponse)
def get_token(user_id: int, token_id: int, db: DbSession):
    """
    Получить конкретный токен по ID
    """
    stmt = select(UserApiToken).where(
        UserApiToken.id == token_id,
        UserApiToken.user_id == user_id
    )
    token = db.execute(stmt).scalar_one_or_none()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Токен не найден"
        )
    
    return token


@router.patch("/{user_id}/tokens/{token_id}", response_model=UserApiTokenResponse)
def update_token(user_id: int, token_id: int, token_data: UserApiTokenUpdate, db: DbSession):
    """
    Обновить токен (описание, активность, значение токена)
    """
    stmt = select(UserApiToken).where(
        UserApiToken.id == token_id,
        UserApiToken.user_id == user_id
    )
    token = db.execute(stmt).scalar_one_or_none()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Токен не найден"
        )
    
    # Обновление полей
    update_data = token_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(token, field, value)
    
    db.commit()
    db.refresh(token)
    
    return token


@router.delete("/{user_id}/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_token(user_id: int, token_id: int, db: DbSession):
    """
    Удалить токен
    """
    stmt = select(UserApiToken).where(
        UserApiToken.id == token_id,
        UserApiToken.user_id == user_id
    )
    token = db.execute(stmt).scalar_one_or_none()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Токен не найден"
        )
    
    db.delete(token)
    db.commit()
    
    return None
