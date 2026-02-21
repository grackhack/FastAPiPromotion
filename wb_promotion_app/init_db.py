#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных и создания первого пользователя
"""
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./wb_promotion.db")

def init_db():
    """Инициализация базы данных - создание таблиц"""
    print(f"Подключение к БД: {DATABASE_URL}")
    
    engine = create_engine(DATABASE_URL)
    
    # Импортируем модели для регистрации метаданных
    from wb_promotion_app.models import Base
    
    # Создаём все таблицы
    Base.metadata.create_all(bind=engine)
    print("[OK] Таблицы успешно созданы!")
    
    return engine


def create_user(engine, username: str, email: str = None, token: str = None):
    """Создание пользователя и optionally токена"""
    
    if not token:
        print("\n[WARN] Предупреждение: токен не указан. Создадим только пользователя.")
        print("Токен можно добавить позже через API: POST /api/users/{id}/tokens\n")
    
    with Session(engine) as session:
        from wb_promotion_app.models import User, UserApiToken
        
        # Проверяем существующего пользователя
        existing_user = session.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"[INFO] Пользователь '{username}' уже существует (ID={existing_user.id})")
            return existing_user.id
        
        # Создаём пользователя
        user = User(username=username, email=email, is_active=True)
        session.add(user)
        session.commit()
        session.refresh(user)
        
        print(f"[OK] Пользователь создан: {username} (ID={user.id})")
        
        # Если есть токен, создаём его
        if token:
            user_token = UserApiToken(
                user_id=user.id,
                token=token,
                description="Initial token",
                is_active=True
            )
            session.add(user_token)
            session.commit()
            print(f"[OK] Токен создан для пользователя {username}")
        
        return user.id


def main():
    print("=" * 50)
    print("Инициализация базы данных WB Promotion App")
    print("=" * 50)
    
    # Инициализация БД
    engine = init_db()
    
    # Создание пользователя (если переданы аргументы)
    if len(sys.argv) >= 2:
        username = sys.argv[1]
        email = sys.argv[2] if len(sys.argv) > 2 else None
        token = sys.argv[3] if len(sys.argv) > 3 else None
        
        create_user(engine, username, email, token)
    else:
        print("\n[OK] База данных инициализирована!")
        print("\nДля создания пользователя используйте:")
        print(f"  {sys.argv[0]} <username> [email] [wb_api_token]")
        print("\nПример:")
        print(f"  {sys.argv[0]} myshop shop@example.com eyJhbGciOiJFUzI1NiIs...")
        print("\nИли создайте пользователя через API:")
        print("  curl -X POST http://localhost:8001/api/users \\")
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"username": "myshop", "email": "shop@example.com"}\'')


if __name__ == "__main__":
    main()
