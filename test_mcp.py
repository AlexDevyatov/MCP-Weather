#!/usr/bin/env python3
"""
Простой скрипт для тестирования MCP Weather сервера через SSE транспорт.

Использование:
    python test_mcp.py
    python test_mcp.py --port 9001
    python test_mcp.py --host your-server.com --port 9001

Требования:
    pip install mcp httpx
"""
import asyncio
import argparse
import httpx
import json
from typing import Optional

try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️  MCP SDK не установлен. Установите: pip install mcp")
    print("   Будет использован упрощенный режим тестирования (только health check)")


async def test_health(client: httpx.AsyncClient, base_url: str) -> bool:
    """Тест health check endpoint."""
    print("🔍 Тест 1: Health Check")
    print(f"   GET {base_url}/health")
    try:
        response = await client.get(f"{base_url}/health", timeout=5.0)
        if response.status_code == 200 and response.text == "OK":
            print(f"   ✅ Успешно: {response.text}")
            return True
        else:
            print(f"   ❌ Ошибка: статус {response.status_code}, ответ: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
        return False


async def test_list_tools_sse(sse_url: str) -> Optional[list]:
    """Тест получения списка инструментов через SSE."""
    if not MCP_AVAILABLE:
        print("   ⚠️  Требуется MCP SDK для этого теста")
        return None
        
    print("\n🔍 Тест 2: Список инструментов (через SSE)")
    print(f"   Подключение к {sse_url}")
    try:
        async with sse_client(sse_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.list_tools()
                
                if result.tools:
                    print(f"   ✅ Найдено инструментов: {len(result.tools)}")
                    for tool in result.tools:
                        print(f"      • {tool.name}: {tool.description}")
                    return result.tools
                else:
                    print("   ⚠️  Инструменты не найдены")
                    return []
                    
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_get_weather_sse(sse_url: str, location: str = "Москва") -> bool:
    """Тест получения текущей погоды через SSE."""
    if not MCP_AVAILABLE:
        print("   ⚠️  Требуется MCP SDK для этого теста")
        return False
        
    print(f"\n🔍 Тест 3: Получение текущей погоды ({location})")
    print(f"   Подключение к {sse_url}")
    try:
        async with sse_client(sse_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "get_current_weather",
                    {"location": location}
                )
                
                if result.content:
                    weather_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                    print(f"   ✅ Успешно получена погода:")
                    print(f"   {'─' * 60}")
                    for line in weather_text.split("\n"):
                        print(f"   {line}")
                    print(f"   {'─' * 60}")
                    return True
                else:
                    print("   ⚠️  Пустой ответ")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_forecast_sse(sse_url: str, location: str = "Санкт-Петербург", days: int = 3) -> bool:
    """Тест получения прогноза погоды через SSE."""
    if not MCP_AVAILABLE:
        print("   ⚠️  Требуется MCP SDK для этого теста")
        return False
        
    print(f"\n🔍 Тест 4: Получение прогноза погоды ({location}, {days} дней)")
    print(f"   Подключение к {sse_url}")
    try:
        async with sse_client(sse_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "get_weather_forecast",
                    {"location": location, "days": days}
                )
                
                if result.content:
                    forecast_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                    print(f"   ✅ Успешно получен прогноз:")
                    print(f"   {'─' * 60}")
                    for line in forecast_text.split("\n")[:10]:
                        print(f"   {line}")
                    if len(forecast_text.split("\n")) > 10:
                        print(f"   ... (показаны первые 10 строк)")
                    print(f"   {'─' * 60}")
                    return True
        return False
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_search_location_sse(sse_url: str, city: str = "Новосибирск") -> bool:
    """Тест поиска местоположения через SSE."""
    if not MCP_AVAILABLE:
        print("   ⚠️  Требуется MCP SDK для этого теста")
        return False
        
    print(f"\n🔍 Тест 5: Поиск местоположения ({city})")
    print(f"   Подключение к {sse_url}")
    try:
        async with sse_client(sse_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "search_location",
                    {"city_name": city}
                )
                
                if result.content:
                    location_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                    print(f"   ✅ Результат поиска:")
                    print(f"   {location_text}")
                    return True
        return False
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    parser = argparse.ArgumentParser(description="Тестирование MCP Weather сервера")
    parser.add_argument("--host", default="localhost", help="Хост сервера (по умолчанию: localhost)")
    parser.add_argument("--port", type=int, default=9001, help="Порт сервера (по умолчанию: 9001)")
    parser.add_argument("--skip-forecast", action="store_true", help="Пропустить тест прогноза")
    parser.add_argument("--skip-search", action="store_true", help="Пропустить тест поиска")
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    sse_url = f"{base_url}/sse"
    
    print("=" * 70)
    print("🧪 Тестирование MCP Weather сервера")
    print("=" * 70)
    print(f"HTTP URL: {base_url}")
    print(f"SSE URL: {sse_url}")
    if not MCP_AVAILABLE:
        print("\n⚠️  MCP SDK не установлен. Установите: pip install mcp")
        print("   Будут выполнены только базовые тесты (health check)")
    print("=" * 70)
    print()
    
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Тест 1: Health check
        results.append(await test_health(client, base_url))
        
        if MCP_AVAILABLE:
            # Тест 2: Список инструментов через SSE
            tools = await test_list_tools_sse(sse_url)
            results.append(tools is not None)
            
            # Тест 3: Текущая погода через SSE
            results.append(await test_get_weather_sse(sse_url))
            
            # Тест 4: Прогноз (опционально)
            if not args.skip_forecast:
                results.append(await test_forecast_sse(sse_url))
            
            # Тест 5: Поиск местоположения (опционально)
            if not args.skip_search:
                results.append(await test_search_location_sse(sse_url))
        else:
            print("\n⚠️  Для полного тестирования установите MCP SDK:")
            print("   pip install mcp")
    
    # Итоги
    print()
    print("=" * 70)
    print("📊 Итоги тестирования")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Пройдено тестов: {passed}/{total}")
    
    if passed == total:
        print("✅ Все тесты пройдены успешно!")
        return 0
    else:
        print("⚠️  Некоторые тесты не прошли")
        if not MCP_AVAILABLE:
            print("\n💡 Совет: Установите MCP SDK для полного тестирования:")
            print("   pip install mcp")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
