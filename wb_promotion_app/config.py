import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Загрузка переменных окружения из файла .env
load_dotenv()

# Конфигурация API
WB_API_TOKEN = os.getenv("WB_API_TOKEN")
if not WB_API_TOKEN:
    raise ValueError("WB_API_TOKEN не найден в переменных окружения (.env)")
WB_BASE_URL = "https://advert-api.wildberries.ru"

# Конфигурация приложения
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
APP_DEBUG = os.getenv("APP_DEBUG", "False").lower() == "true"

# Конфигурация логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Конфигурация базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./wb_promotion.db")

# Создание движка SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=APP_DEBUG  # Логирование SQL запросов в режиме отладки
)

# Session factory для использования в приложении
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Зависимость для получения сессии базы данных.
    Автоматически закрывает сессию после использования.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()