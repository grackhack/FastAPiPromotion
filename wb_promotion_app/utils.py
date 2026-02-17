from typing import Dict, Any, List
import logging


class RateLimitError(Exception):
    """
    Исключение при превышении лимита запросов к API
    """
    pass


def setup_logging(level: str = "INFO"):
    """
    Настройка логирования для приложения
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def validate_token(token: str) -> bool:
    """
    Проверка валидности токена API
    """
    if not token or len(token) == 0:
        return False
    # Простая проверка длины токена (в реальном приложении может быть сложнее)
    return len(token) >= 32


def format_response(data: Any) -> Dict[str, Any]:
    """
    Форматирование ответа API
    """
    return {
        "success": True,
        "data": data
    }


def handle_api_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """
    Обработка ошибок API
    """
    logging.error(f"API Error in {context}: {str(error)}")
    return {
        "success": False,
        "error": str(error),
        "context": context
    }


def clean_query(query: str) -> str:
    """
    Очистка поискового запроса от лишних символов
    """
    # Удаление лишних пробелов и специальных символов
    cleaned = query.strip().lower()
    # Здесь можно добавить дополнительную логику очистки
    return cleaned