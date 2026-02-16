import os
from dotenv import load_dotenv

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