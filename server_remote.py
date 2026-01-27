"""MCP-сервер для удаленного развертывания через SSE (Server-Sent Events).

Использование:
    python server_remote.py --host 0.0.0.0 --port 8000
    python server_remote.py --host 0.0.0.0 --port 8000 --workers 4

Сервер будет доступен по адресу: http://host:port/sse
"""
import asyncio
import logging
import sys
import click
from typing import Any, Optional

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
import uvicorn

from config import Config
from weather.provider import WeatherProvider
from weather.formatter import WeatherFormatter
from weather.cache import WeatherCache

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Инициализация компонентов
Config.validate()
weather_provider = WeatherProvider()
weather_formatter = WeatherFormatter()
weather_cache = WeatherCache(ttl=Config.CACHE_TTL)

# Создание MCP-сервера
app = Server("weather-mcp-server")


async def parse_location(location: Optional[str]) -> tuple[float, float]:
    """
    Парсинг местоположения из строки или использование значения по умолчанию.
    
    Args:
        location: Строка с координатами "lat,lon" или название города
        
    Returns:
        Кортеж (широта, долгота)
    """
    if location:
        # Попытка распарсить как координаты
        if "," in location:
            try:
                parts = location.split(",")
                return float(parts[0].strip()), float(parts[1].strip())
            except ValueError:
                pass
        
        # Попытка найти по названию города
        result = await weather_provider.geocode_location(location)
        if result:
            return result[0], result[1]
    
    # Использование значения по умолчанию
    default_parts = Config.DEFAULT_LOCATION.split(",")
    return float(default_parts[0]), float(default_parts[1])


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """Список доступных инструментов."""
    return [
        types.Tool(
            name="get_current_weather",
            description="Получение текущей погоды для указанного местоположения",
            input_schema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Название города или координаты в формате 'lat,lon' (опционально)"
                    },
                    "lat": {
                        "type": "number",
                        "description": "Широта (опционально, если не указан location)"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Долгота (опционально, если не указан location)"
                    }
                }
            }
        ),
        types.Tool(
            name="get_weather_forecast",
            description="Получение прогноза погоды на несколько дней",
            input_schema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Количество дней прогноза (по умолчанию 3, максимум 16)",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 16
                    },
                    "location": {
                        "type": "string",
                        "description": "Название города или координаты в формате 'lat,lon' (опционально)"
                    },
                    "lat": {
                        "type": "number",
                        "description": "Широта (опционально, если не указан location)"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Долгота (опционально, если не указан location)"
                    }
                }
            }
        ),
        types.Tool(
            name="search_location",
            description="Поиск координат по названию города",
            input_schema={
                "type": "object",
                "properties": {
                    "city_name": {
                        "type": "string",
                        "description": "Название города для поиска"
                    }
                },
                "required": ["city_name"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Обработка вызовов инструментов."""
    try:
        if name == "get_current_weather":
            # Определение координат
            if "lat" in arguments and "lon" in arguments:
                lat, lon = float(arguments["lat"]), float(arguments["lon"])
            else:
                location = arguments.get("location")
                lat, lon = await parse_location(location)
            
            # Проверка кэша
            cached = weather_cache.get(lat, lon, "current")
            if cached:
                logger.info(f"Использован кэш для координат {lat}, {lon}")
                return [types.TextContent(type="text", text=cached)]
            
            # Получение данных
            data = await weather_provider.get_current_weather(lat, lon, Config.DEFAULT_LANG)
            formatted = weather_formatter.format_current_weather(data)
            
            # Сохранение в кэш
            weather_cache.set(lat, lon, formatted, "current")
            
            return [types.TextContent(type="text", text=formatted)]
        
        elif name == "get_weather_forecast":
            # Определение координат
            if "lat" in arguments and "lon" in arguments:
                lat, lon = float(arguments["lat"]), float(arguments["lon"])
            else:
                location = arguments.get("location")
                lat, lon = await parse_location(location)
            
            days = min(max(int(arguments.get("days", 3)), 1), 16)
            
            # Проверка кэша
            cache_key = f"{days}days"
            cached = weather_cache.get(lat, lon, f"forecast_{cache_key}")
            if cached:
                logger.info(f"Использован кэш для прогноза {lat}, {lon}, {days} дней")
                return [types.TextContent(type="text", text=cached)]
            
            # Получение данных
            data = await weather_provider.get_forecast(lat, lon, days, Config.DEFAULT_LANG)
            formatted = weather_formatter.format_forecast(data, days)
            
            # Сохранение в кэш
            weather_cache.set(lat, lon, formatted, f"forecast_{cache_key}")
            
            return [types.TextContent(type="text", text=formatted)]
        
        elif name == "search_location":
            city_name = arguments.get("city_name")
            if not city_name:
                return [types.TextContent(
                    type="text",
                    text="Ошибка: не указано название города"
                )]
            
            result = await weather_provider.geocode_location(city_name)
            if result:
                lat, lon, full_name = result
                return [types.TextContent(
                    type="text",
                    text=f"📍 {full_name}\nКоординаты: {lat}, {lon}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Город '{city_name}' не найден"
                )]
        
        else:
            raise ValueError(f"Неизвестный инструмент: {name}")
    
    except ValueError as e:
        logger.error(f"Ошибка валидации: {e}")
        return [types.TextContent(type="text", text=f"Ошибка: {str(e)}")]
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Произошла ошибка: {str(e)}")]


@app.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    """Список доступных промптов."""
    return [
        types.Prompt(
            name="current_weather",
            description="Быстрое получение текущей погоды",
            arguments=[
                types.PromptArgument(
                    name="location",
                    description="Название города или координаты (опционально)",
                    required=False
                )
            ]
        ),
        types.Prompt(
            name="weather_forecast",
            description="Получение прогноза погоды",
            arguments=[
                types.PromptArgument(
                    name="location",
                    description="Название города или координаты (опционально)",
                    required=False
                ),
                types.PromptArgument(
                    name="days",
                    description="Количество дней прогноза (по умолчанию 3)",
                    required=False
                )
            ]
        ),
        types.Prompt(
            name="weather_summary",
            description="Сводка погоды с рекомендациями",
            arguments=[
                types.PromptArgument(
                    name="location",
                    description="Название города или координаты (опционально)",
                    required=False
                )
            ]
        )
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, Any]) -> list[types.PromptMessage]:
    """Обработка запросов промптов."""
    if name == "current_weather":
        location = arguments.get("location", "")
        if location:
            prompt_text = f"Получи текущую погоду для {location} используя инструмент get_current_weather"
        else:
            prompt_text = "Получи текущую погоду используя инструмент get_current_weather"
        return [types.PromptMessage(
            role="user",
            content=[types.TextContent(type="text", text=prompt_text)]
        )]
    
    elif name == "weather_forecast":
        location = arguments.get("location", "")
        days = arguments.get("days", "3")
        if location:
            prompt_text = f"Получи прогноз погоды на {days} дней для {location} используя инструмент get_weather_forecast"
        else:
            prompt_text = f"Получи прогноз погоды на {days} дней используя инструмент get_weather_forecast"
        return [types.PromptMessage(
            role="user",
            content=[types.TextContent(type="text", text=prompt_text)]
        )]
    
    elif name == "weather_summary":
        location = arguments.get("location", "")
        if location:
            prompt_text = f"Получи текущую погоду для {location} используя инструмент get_current_weather и предоставь сводку с рекомендациями"
        else:
            prompt_text = "Получи текущую погоду используя инструмент get_current_weather и предоставь сводку с рекомендациями"
        return [types.PromptMessage(
            role="user",
            content=[types.TextContent(type="text", text=prompt_text)]
        )]
    
    else:
        raise ValueError(f"Неизвестный промпт: {name}")


@click.command()
@click.option("--host", default="0.0.0.0", help="Host для привязки сервера")
@click.option("--port", default=8000, help="Порт для привязки сервера")
@click.option("--workers", default=1, help="Количество worker процессов")
def main(host: str, port: int, workers: int) -> None:
    """Запуск MCP-сервера через SSE транспорт."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
        return Response()

    async def health_check(request: Request):
        """Health check endpoint."""
        return Response("OK", status_code=200)

    starlette_app = Starlette(
        debug=False,
        routes=[
            Route("/health", endpoint=health_check, methods=["GET"]),
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    logger.info(f"Запуск MCP-сервера на http://{host}:{port}")
    logger.info(f"SSE endpoint: http://{host}:{port}/sse")
    logger.info(f"Messages endpoint: http://{host}:{port}/messages/")
    
    uvicorn.run(starlette_app, host=host, port=port, workers=workers)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Сервер остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
