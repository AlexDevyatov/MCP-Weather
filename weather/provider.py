"""Провайдер для работы с API Яндекс Погоды."""
import aiohttp
from typing import Dict, Any, Optional, Tuple
import logging

from config import Config

logger = logging.getLogger(__name__)


class WeatherProvider:
    """Класс для получения данных о погоде из Яндекс Погоды API."""
    
    def __init__(self, api_key: str):
        """
        Инициализация провайдера.
        
        Args:
            api_key: API ключ Яндекс Погоды
        """
        self.api_key = api_key
        self.base_url = Config.YANDEX_API_URL
        self.timeout = aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
    
    async def get_weather(
        self,
        lat: float,
        lon: float,
        lang: str = "ru_RU",
        limit: int = 1,
        hours: bool = False,
        extra: bool = False
    ) -> Dict[str, Any]:
        """
        Получение данных о погоде.
        
        Args:
            lat: Широта
            lon: Долгота
            lang: Язык ответа
            limit: Количество дней прогноза
            hours: Включить почасовой прогноз
            extra: Дополнительные данные
            
        Returns:
            Словарь с данными о погоде
            
        Raises:
            ValueError: При ошибках API
            aiohttp.ClientError: При ошибках сети
        """
        params = {
            "lat": lat,
            "lon": lon,
            "lang": lang,
            "limit": limit,
        }
        
        if hours:
            params["hours"] = "true"
        if extra:
            params["extra"] = "true"
        
        headers = {
            "X-Yandex-API-Key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 401:
                        raise ValueError("Неверный API ключ Яндекс Погоды")
                    elif response.status == 403:
                        raise ValueError("Доступ запрещён. Проверьте API ключ")
                    elif response.status == 429:
                        raise ValueError("Превышен лимит запросов. Попробуйте позже")
                    elif response.status == 500:
                        raise ValueError("Ошибка сервера Яндекс Погоды")
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка API: {response.status} - {error_text}")
                        raise ValueError(f"Ошибка API: {response.status}")
        
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети: {e}")
            raise ValueError(f"Ошибка сети: {str(e)}")
    
    async def get_current_weather(
        self,
        lat: float,
        lon: float,
        lang: str = "ru_RU"
    ) -> Dict[str, Any]:
        """
        Получение текущей погоды.
        
        Args:
            lat: Широта
            lon: Долгота
            lang: Язык ответа
            
        Returns:
            Словарь с данными о текущей погоде
        """
        return await self.get_weather(lat, lon, lang=lang, limit=1)
    
    async def get_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 3,
        lang: str = "ru_RU"
    ) -> Dict[str, Any]:
        """
        Получение прогноза погоды.
        
        Args:
            lat: Широта
            lon: Долгота
            days: Количество дней прогноза
            lang: Язык ответа
            
        Returns:
            Словарь с данными о прогнозе
        """
        return await self.get_weather(lat, lon, lang=lang, limit=days)
    
    async def geocode_location(self, city_name: str) -> Optional[Tuple[float, float, str]]:
        """
        Поиск координат по названию города.
        
        Примечание: Яндекс Погода API не предоставляет геокодинг.
        Используется упрощённая реализация с популярными городами.
        
        Args:
            city_name: Название города
            
        Returns:
            Кортеж (широта, долгота, полное название) или None
        """
        # База популярных городов России
        cities = {
            "москва": (55.75396, 37.620393, "Москва"),
            "санкт-петербург": (59.9342802, 30.3350986, "Санкт-Петербург"),
            "новосибирск": (55.0083526, 82.9357327, "Новосибирск"),
            "екатеринбург": (56.8430993, 60.6454086, "Екатеринбург"),
            "казань": (55.8304307, 49.0660806, "Казань"),
            "нижний новгород": (56.2965039, 43.936059, "Нижний Новгород"),
            "челябинск": (55.1644419, 61.4368432, "Челябинск"),
            "самара": (53.2000663, 50.15, "Самара"),
            "омск": (54.9884806, 73.3242362, "Омск"),
            "ростов-на-дону": (47.2357137, 39.701505, "Ростов-на-Дону"),
            "уфа": (54.734768, 55.9578387, "Уфа"),
            "красноярск": (56.01839, 92.86717, "Красноярск"),
            "воронеж": (51.67204, 39.1843, "Воронеж"),
            "пермь": (58.01046, 56.25017, "Пермь"),
            "волгоград": (48.71939, 44.50183, "Волгоград"),
        }
        
        city_lower = city_name.lower().strip()
        
        # Прямое совпадение
        if city_lower in cities:
            return cities[city_lower]
        
        # Частичное совпадение
        for key, value in cities.items():
            if city_lower in key or key in city_lower:
                return value
        
        return None
