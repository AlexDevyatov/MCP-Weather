"""Конфигурация MCP-сервера погоды."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Настройки приложения."""
    
    # URL API Open-Meteo
    OPEN_METEO_FORECAST_URL: str = "https://api.open-meteo.com/v1/forecast"
    OPEN_METEO_GEOCODING_URL: str = "https://geocoding-api.open-meteo.com/v1/search"
    
    # Язык по умолчанию
    DEFAULT_LANG: str = os.getenv("DEFAULT_LANG", "ru")
    
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
        # Open-Meteo не требует API ключа, поэтому валидация не нужна
        pass
