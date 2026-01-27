"""Форматирование данных о погоде."""
from typing import Dict, Any, List
from datetime import datetime


class WeatherFormatter:
    """Класс для форматирования данных о погоде."""
    
    # Словарь условий погоды
    CONDITIONS = {
        "clear": "ясно",
        "partly-cloudy": "малооблачно",
        "cloudy": "облачно с прояснениями",
        "overcast": "пасмурно",
        "drizzle": "морось",
        "light-rain": "небольшой дождь",
        "rain": "дождь",
        "moderate-rain": "умеренно сильный дождь",
        "heavy-rain": "сильный дождь",
        "continuous-heavy-rain": "длительный сильный дождь",
        "showers": "ливень",
        "wet-snow": "дождь со снегом",
        "light-snow": "небольшой снег",
        "snow": "снег",
        "snow-showers": "снегопад",
        "hail": "град",
        "thunderstorm": "гроза",
        "thunderstorm-with-rain": "дождь с грозой",
        "thunderstorm-with-hail": "гроза с градом",
    }
    
    # Словарь направлений ветра
    WIND_DIRECTIONS = {
        "nw": "северо-западный",
        "n": "северный",
        "ne": "северо-восточный",
        "e": "восточный",
        "se": "юго-восточный",
        "s": "южный",
        "sw": "юго-западный",
        "w": "западный",
        "c": "штиль",
    }
    
    # Эмодзи для условий
    CONDITION_EMOJIS = {
        "clear": "☀️",
        "partly-cloudy": "⛅",
        "cloudy": "☁️",
        "overcast": "☁️",
        "drizzle": "🌦️",
        "light-rain": "🌦️",
        "rain": "🌧️",
        "moderate-rain": "🌧️",
        "heavy-rain": "🌧️",
        "continuous-heavy-rain": "🌧️",
        "showers": "🌧️",
        "wet-snow": "🌨️",
        "light-snow": "🌨️",
        "snow": "❄️",
        "snow-showers": "❄️",
        "hail": "🌨️",
        "thunderstorm": "⛈️",
        "thunderstorm-with-rain": "⛈️",
        "thunderstorm-with-hail": "⛈️",
    }
    
    @classmethod
    def translate_condition(cls, condition: str) -> str:
        """Перевод условия погоды на русский."""
        return cls.CONDITIONS.get(condition, condition)
    
    @classmethod
    def translate_wind_direction(cls, direction: str) -> str:
        """Перевод направления ветра на русский."""
        return cls.WIND_DIRECTIONS.get(direction.lower(), direction)
    
    @classmethod
    def get_condition_emoji(cls, condition: str) -> str:
        """Получение эмодзи для условия погоды."""
        return cls.CONDITION_EMOJIS.get(condition, "🌤️")
    
    @classmethod
    def format_current_weather(cls, data: Dict[str, Any]) -> str:
        """
        Форматирование текущей погоды в красивый текст.
        
        Args:
            data: Данные о погоде из API
            
        Returns:
            Отформатированная строка
        """
        fact = data.get("fact", {})
        info = data.get("info", {})
        
        location = info.get("tzinfo", {}).get("name", "Неизвестно")
        temp = fact.get("temp", 0)
        feels_like = fact.get("feels_like", 0)
        condition = cls.translate_condition(fact.get("condition", ""))
        humidity = fact.get("humidity", 0)
        pressure_mm = fact.get("pressure_mm", 0)
        wind_speed = fact.get("wind_speed", 0)
        wind_dir = cls.translate_wind_direction(fact.get("wind_dir", ""))
        icon = fact.get("icon", "")
        emoji = cls.get_condition_emoji(fact.get("condition", ""))
        
        # Время обновления
        now = datetime.now()
        updated_at = now.strftime("%H:%M")
        
        # Рекомендации
        recommendation = cls._get_recommendation(temp, condition, fact.get("prec_type", 0))
        
        result = f"""{emoji} Погода в {location}
━━━━━━━━━━━━━━━━━━━━━━━
🌡️  Температура: {temp}°C (ощущается как {feels_like}°C)
☁️  Условия: {condition}
💧 Влажность: {humidity}%
📊 Давление: {pressure_mm} мм рт.ст.
💨 Ветер: {wind_speed} м/с, {wind_dir}
🕐 Обновлено: {updated_at}

💡 Рекомендация: {recommendation}"""
        
        return result
    
    @classmethod
    def format_forecast(cls, data: Dict[str, Any], days: int = 3) -> str:
        """
        Форматирование прогноза погоды.
        
        Args:
            data: Данные о прогнозе из API
            days: Количество дней
            
        Returns:
            Отформатированная строка
        """
        info = data.get("info", {})
        forecasts = data.get("forecasts", [])[:days]
        
        location = info.get("tzinfo", {}).get("name", "Неизвестно")
        
        result = f"📅 Прогноз погоды в {location} на {len(forecasts)} дней\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for forecast in forecasts:
            date_str = forecast.get("date", "")
            parts = forecast.get("parts", {})
            day = parts.get("day", {})
            
            # Парсинг даты
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                date_formatted = date_obj.strftime("%d.%m.%Y")
                weekday = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][date_obj.weekday()]
            except:
                date_formatted = date_str
                weekday = ""
            
            temp_min = day.get("temp_min", 0)
            temp_max = day.get("temp_max", 0)
            condition = cls.translate_condition(day.get("condition", ""))
            prec_mm = day.get("prec_mm", 0)
            humidity = day.get("humidity", 0)
            emoji = cls.get_condition_emoji(day.get("condition", ""))
            
            result += f"{emoji} {date_formatted} ({weekday})\n"
            result += f"   🌡️  {temp_min}°C / {temp_max}°C\n"
            result += f"   ☁️  {condition}\n"
            if prec_mm > 0:
                result += f"   🌧️  Осадки: {prec_mm} мм\n"
            result += f"   💧 Влажность: {humidity}%\n\n"
        
        return result.strip()
    
    @classmethod
    def _get_recommendation(cls, temp: int, condition: str, prec_type: int) -> str:
        """
        Генерация рекомендации на основе погоды.
        
        Args:
            temp: Температура
            condition: Условия погоды
            prec_type: Тип осадков (0 - нет, 1 - дождь, 2 - дождь со снегом, 3 - снег)
            
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
        
        # Рекомендации по осадкам
        if prec_type == 1 or "дождь" in condition.lower() or "ливень" in condition.lower():
            recommendations.append("и обязательно возьмите зонт! ☂️")
        elif prec_type == 3 or "снег" in condition.lower():
            recommendations.append("и наденьте тёплую обувь")
        elif prec_type == 2:
            recommendations.append("и будьте осторожны на дорогах")
        
        return " ".join(recommendations) if recommendations else "Обычная погода"
