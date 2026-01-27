"""Провайдер для работы с Open-Meteo Weather API."""
import aiohttp
from typing import Dict, Any, Optional, Tuple
import logging

from config import Config

logger = logging.getLogger(__name__)


class WeatherProvider:
    """Класс для получения данных о погоде из Open-Meteo API."""
    
    def __init__(self):
        """Инициализация провайдера."""
        self.forecast_url = Config.OPEN_METEO_FORECAST_URL
        self.geocoding_url = Config.OPEN_METEO_GEOCODING_URL
        self.timeout = aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
    
    async def get_current_weather(
        self,
        lat: float,
        lon: float,
        lang: str = "ru"
    ) -> Dict[str, Any]:
        """
        Получение текущей погоды.
        
        Args:
            lat: Широта
            lon: Долгота
            lang: Язык ответа (ru, en, etc.)
            
        Returns:
            Словарь с данными о текущей погоде
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl",
            "timezone": "auto",
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.forecast_url,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 400:
                        error_text = await response.text()
                        logger.error(f"Ошибка API: {response.status} - {error_text}")
                        raise ValueError("Неверные параметры запроса")
                    elif response.status == 429:
                        raise ValueError("Превышен лимит запросов. Попробуйте позже")
                    elif response.status >= 500:
                        raise ValueError("Ошибка сервера Open-Meteo")
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка API: {response.status} - {error_text}")
                        raise ValueError(f"Ошибка API: {response.status}")
        
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети: {e}")
            raise ValueError(f"Ошибка сети: {str(e)}")
    
    async def get_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 3,
        lang: str = "ru"
    ) -> Dict[str, Any]:
        """
        Получение прогноза погоды.
        
        Args:
            lat: Широта
            lon: Долгота
            days: Количество дней прогноза (1-16)
            lang: Язык ответа
            
        Returns:
            Словарь с данными о прогнозе
        """
        days = min(max(days, 1), 16)  # Open-Meteo поддерживает до 16 дней
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_max",
            "timezone": "auto",
            "forecast_days": days,
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.forecast_url,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 400:
                        error_text = await response.text()
                        logger.error(f"Ошибка API: {response.status} - {error_text}")
                        raise ValueError("Неверные параметры запроса")
                    elif response.status == 429:
                        raise ValueError("Превышен лимит запросов. Попробуйте позже")
                    elif response.status >= 500:
                        raise ValueError("Ошибка сервера Open-Meteo")
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка API: {response.status} - {error_text}")
                        raise ValueError(f"Ошибка API: {response.status}")
        
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети: {e}")
            raise ValueError(f"Ошибка сети: {str(e)}")
    
    async def geocode_location(self, city_name: str) -> Optional[Tuple[float, float, str]]:
        """
        Поиск координат по названию города через Open-Meteo Geocoding API.
        
        Args:
            city_name: Название города
            
        Returns:
            Кортеж (широта, долгота, полное название) или None
        """
        params = {
            "name": city_name,
            "count": 1,
            "language": "ru",
            "format": "json"
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.geocoding_url,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        if results:
                            result = results[0]
                            lat = result.get("latitude")
                            lon = result.get("longitude")
                            name = result.get("name", city_name)
                            country = result.get("country", "")
                            admin1 = result.get("admin1", "")  # Регион/область
                            
                            full_name = name
                            if admin1:
                                full_name = f"{name}, {admin1}"
                            if country:
                                full_name = f"{name}, {country}"
                            
                            return (lat, lon, full_name)
                        return None
                    else:
                        logger.warning(f"Ошибка геокодинга: {response.status}")
                        return None
        
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети при геокодинге: {e}")
            return None
