"""Конфигурация MCP-сервера погоды."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Настройки приложения."""
    
    # API ключ Яндекс Погоды
    YANDEX_API_KEY: str = os.getenv("YANDEX_API_KEY", "")
    
    # URL API Яндекс Погоды
    YANDEX_API_URL: str = "https://api.weather.yandex.ru/v2/forecast"
    
    # Язык по умолчанию
    DEFAULT_LANG: str = os.getenv("DEFAULT_LANG", "ru_RU")
    
    # Местоположение по умолчанию (Москва)
    DEFAULT_LOCATION: str = os.getenv("DEFAULT_LOCATION", "55.75396,37.620393")
    
    # Время жизни кэша в секундах (10 минут)
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "600"))
    
    # Уровень логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Таймаут запросов к API
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "10"))
    
    @classmethod
    def validate(cls) -> None:
        """Проверка наличия обязательных настроек."""
        if not cls.YANDEX_API_KEY:
            raise ValueError(
                "YANDEX_API_KEY не установлен. "
                "Установите его в переменных окружения или в .env файле."
            )
