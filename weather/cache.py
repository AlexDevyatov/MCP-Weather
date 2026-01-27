"""Кэширование запросов погоды."""
import time
from typing import Dict, Optional, Tuple, Any


class WeatherCache:
    """In-memory кэш для результатов запросов погоды."""
    
    def __init__(self, ttl: int = 600):
        """
        Инициализация кэша.
        
        Args:
            ttl: Время жизни записей в секундах (по умолчанию 10 минут)
        """
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._ttl = ttl
    
    def _make_key(self, lat: float, lon: float, cache_type: str = "current") -> str:
        """Создание ключа кэша."""
        return f"{cache_type}:{lat:.4f}:{lon:.4f}"
    
    def get(self, lat: float, lon: float, cache_type: str = "current") -> Optional[Any]:
        """
        Получение значения из кэша.
        
        Args:
            lat: Широта
            lon: Долгота
            cache_type: Тип кэша ('current' или 'forecast')
            
        Returns:
            Кэшированное значение или None, если его нет или оно устарело
        """
        key = self._make_key(lat, lon, cache_type)
        if key not in self._cache:
            return None
        
        timestamp, value = self._cache[key]
        if time.time() - timestamp > self._ttl:
            del self._cache[key]
            return None
        
        return value
    
    def set(self, lat: float, lon: float, value: Any, cache_type: str = "current") -> None:
        """
        Сохранение значения в кэш.
        
        Args:
            lat: Широта
            lon: Долгота
            value: Значение для кэширования
            cache_type: Тип кэша ('current' или 'forecast')
        """
        key = self._make_key(lat, lon, cache_type)
        self._cache[key] = (time.time(), value)
    
    def clear(self) -> None:
        """Очистка кэша."""
        self._cache.clear()
    
    def cleanup(self) -> None:
        """Удаление устаревших записей из кэша."""
        current_time = time.time()
        keys_to_delete = [
            key for key, (timestamp, _) in self._cache.items()
            if current_time - timestamp > self._ttl
        ]
        for key in keys_to_delete:
            del self._cache[key]
