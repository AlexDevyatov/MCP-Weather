"""Форматирование данных о погоде."""
from typing import Dict, Any
from datetime import datetime


class WeatherFormatter:
    """Класс для форматирования данных о погоде."""
    
    # WMO Weather interpretation codes (Open-Meteo использует эти коды)
    # Источник: https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
    WMO_WEATHER_CODES = {
        0: ("ясно", "☀️"),
        1: ("преимущественно ясно", "🌤️"),
        2: ("переменная облачность", "⛅"),
        3: ("пасмурно", "☁️"),
        45: ("туман", "🌫️"),
        48: ("осаждающийся иней туман", "🌫️"),
        51: ("лёгкая морось", "🌦️"),
        53: ("умеренная морось", "🌦️"),
        55: ("сильная морось", "🌦️"),
        56: ("лёгкая ледяная морось", "🌨️"),
        57: ("сильная ледяная морось", "🌨️"),
        61: ("небольшой дождь", "🌧️"),
        63: ("умеренный дождь", "🌧️"),
        65: ("сильный дождь", "🌧️"),
        66: ("лёгкий ледяной дождь", "🌨️"),
        67: ("сильный ледяной дождь", "🌨️"),
        71: ("небольшой снег", "❄️"),
        73: ("умеренный снег", "❄️"),
        75: ("сильный снег", "❄️"),
        77: ("снежные зёрна", "❄️"),
        80: ("небольшой ливень", "🌧️"),
        81: ("умеренный ливень", "🌧️"),
        82: ("сильный ливень", "🌧️"),
        85: ("небольшой снегопад", "❄️"),
        86: ("сильный снегопад", "❄️"),
        95: ("гроза", "⛈️"),
        96: ("гроза с небольшим градом", "⛈️"),
        99: ("гроза с сильным градом", "⛈️"),
    }
    
    # Направления ветра (градусы)
    WIND_DIRECTIONS = {
        (0, 22.5): "северный",
        (22.5, 67.5): "северо-восточный",
        (67.5, 112.5): "восточный",
        (112.5, 157.5): "юго-восточный",
        (157.5, 202.5): "южный",
        (202.5, 247.5): "юго-западный",
        (247.5, 292.5): "западный",
        (292.5, 337.5): "северо-западный",
        (337.5, 360): "северный",
    }
    
    @classmethod
    def get_weather_condition(cls, weather_code: int) -> tuple[str, str]:
        """
        Получение условия погоды по WMO коду.
        
        Args:
            weather_code: WMO Weather interpretation code
            
        Returns:
            Кортеж (название, эмодзи)
        """
        return cls.WMO_WEATHER_CODES.get(weather_code, ("неизвестно", "🌤️"))
    
    @classmethod
    def get_wind_direction(cls, degrees: float) -> str:
        """
        Получение направления ветра по градусам.
        
        Args:
            degrees: Направление в градусах (0-360)
            
        Returns:
            Название направления
        """
        for (start, end), direction in cls.WIND_DIRECTIONS.items():
            if start <= degrees < end or (start > end and (degrees >= start or degrees < end)):
                return direction
        return "неизвестно"
    
    @classmethod
    def format_current_weather(cls, data: Dict[str, Any]) -> str:
        """
        Форматирование текущей погоды в красивый текст.
        
        Args:
            data: Данные о погоде из Open-Meteo API
            
        Returns:
            Отформатированная строка
        """
        current = data.get("current", {})
        latitude = data.get("latitude", 0)
        longitude = data.get("longitude", 0)
        
        # Формируем название местоположения
        location = f"{latitude:.2f}°N, {longitude:.2f}°E"
        
        temp = round(current.get("temperature_2m", 0))
        weather_code = current.get("weather_code", 0)
        humidity = current.get("relative_humidity_2m", 0)
        pressure_hpa = current.get("pressure_msl", 0)
        pressure_mm = round(pressure_hpa * 0.750062) if pressure_hpa else 0
        wind_speed = current.get("wind_speed_10m", 0)
        wind_direction_deg = current.get("wind_direction_10m", 0)
        wind_dir = cls.get_wind_direction(wind_direction_deg)
        
        condition, emoji = cls.get_weather_condition(weather_code)
        
        # Время обновления
        time_str = current.get("time", "")
        if time_str:
            try:
                time_obj = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                updated_at = time_obj.strftime("%H:%M")
            except:
                updated_at = datetime.now().strftime("%H:%M")
        else:
            updated_at = datetime.now().strftime("%H:%M")
        
        # Рекомендации
        recommendation = cls._get_recommendation(temp, condition, weather_code)
        
        result = f"""{emoji} Погода в {location}
━━━━━━━━━━━━━━━━━━━━━━━
🌡️  Температура: {temp}°C
☁️  Условия: {condition}
💧 Влажность: {humidity}%
📊 Давление: {pressure_mm} мм рт.ст.
💨 Ветер: {wind_speed:.1f} м/с, {wind_dir}
🕐 Обновлено: {updated_at}

💡 Рекомендация: {recommendation}"""
        
        return result
    
    @classmethod
    def format_forecast(cls, data: Dict[str, Any], days: int = 3) -> str:
        """
        Форматирование прогноза погоды.
        
        Args:
            data: Данные о прогнозе из Open-Meteo API
            days: Количество дней
            
        Returns:
            Отформатированная строка
        """
        daily = data.get("daily", {})
        latitude = data.get("latitude", 0)
        longitude = data.get("longitude", 0)
        
        location = f"{latitude:.2f}°N, {longitude:.2f}°E"
        
        times = daily.get("time", [])[:days]
        weather_codes = daily.get("weather_code", [])[:days]
        temp_max = daily.get("temperature_2m_max", [])[:days]
        temp_min = daily.get("temperature_2m_min", [])[:days]
        precipitation = daily.get("precipitation_sum", [])[:days]
        humidity = daily.get("relative_humidity_2m_max", [])[:days]
        
        result = f"📅 Прогноз погоды в {location} на {len(times)} дней\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, time_str in enumerate(times):
            # Парсинг даты
            try:
                date_obj = datetime.fromisoformat(time_str)
                date_formatted = date_obj.strftime("%d.%m.%Y")
                weekday = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][date_obj.weekday()]
            except:
                date_formatted = time_str
                weekday = ""
            
            code = weather_codes[i] if i < len(weather_codes) else 0
            condition, emoji = cls.get_weather_condition(code)
            temp_max_val = round(temp_max[i]) if i < len(temp_max) else 0
            temp_min_val = round(temp_min[i]) if i < len(temp_min) else 0
            prec_mm = precipitation[i] if i < len(precipitation) else 0
            humidity_val = round(humidity[i]) if i < len(humidity) else 0
            
            result += f"{emoji} {date_formatted} ({weekday})\n"
            result += f"   🌡️  {temp_min_val}°C / {temp_max_val}°C\n"
            result += f"   ☁️  {condition}\n"
            if prec_mm > 0:
                result += f"   🌧️  Осадки: {prec_mm:.1f} мм\n"
            result += f"   💧 Влажность: {humidity_val}%\n\n"
        
        return result.strip()
    
    @classmethod
    def _get_recommendation(cls, temp: float, condition: str, weather_code: int) -> str:
        """
        Генерация рекомендации на основе погоды.
        
        Args:
            temp: Температура
            condition: Условия погоды
            weather_code: WMO код погоды
            
        Returns:
            Рекомендация
        """
        recommendations = []
        
        # Рекомендации по температуре
        if temp < -10:
            recommendations.append("Очень холодно! Наденьте тёплую зимнюю одежду")
        elif temp < 0:
            recommendations.append("Холодно. Наденьте тёплую куртку")
        elif temp < 10:
            recommendations.append("Прохладно. Возьмите куртку")
        elif temp < 20:
            recommendations.append("Возьмите лёгкую куртку или свитер")
        elif temp < 25:
            recommendations.append("Тепло. Лёгкая одежда будет комфортна")
        else:
            recommendations.append("Жарко. Лёгкая одежда")
        
        # Рекомендации по осадкам (коды 51-67, 80-82, 95-99)
        if weather_code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
            recommendations.append("и обязательно возьмите зонт! ☂️")
        elif weather_code in [71, 73, 75, 77, 85, 86]:
            recommendations.append("и наденьте тёплую обувь")
        elif weather_code in [95, 96, 99]:
            recommendations.append("и будьте осторожны на улице")
        
        return " ".join(recommendations) if recommendations else "Обычная погода"
