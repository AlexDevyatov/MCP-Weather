#!/usr/bin/env python3
"""
Простой скрипт для тестирования MCP Weather сервера через HTTP API.

Использование:
    python test_mcp.py
    python test_mcp.py --port 9001
    python test_mcp.py --host your-server.com --port 9001
"""
import asyncio
import argparse
import httpx
import json
from typing import Optional


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


async def test_list_tools(client: httpx.AsyncClient, base_url: str) -> Optional[list]:
    """Тест получения списка инструментов."""
    print("\n🔍 Тест 2: Список инструментов")
    print(f"   POST {base_url}/messages/")
    try:
        response = await client.post(
            f"{base_url}/messages/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            },
            timeout=10.0
        )
        
        if response.status_code != 200:
            print(f"   ❌ Ошибка HTTP: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return None
        
        data = response.json()
        
        if "error" in data:
            print(f"   ❌ Ошибка MCP: {data['error']}")
            return None
        
        if "result" in data and "tools" in data["result"]:
            tools = data["result"]["tools"]
            print(f"   ✅ Найдено инструментов: {len(tools)}")
            for tool in tools:
                print(f"      • {tool['name']}: {tool['description']}")
            return tools
        else:
            print(f"   ⚠️  Неожиданный формат ответа: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return None
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return None


async def test_get_weather(client: httpx.AsyncClient, base_url: str, location: str = "Москва") -> bool:
    """Тест получения текущей погоды."""
    print(f"\n🔍 Тест 3: Получение текущей погоды ({location})")
    print(f"   POST {base_url}/messages/")
    try:
        response = await client.post(
            f"{base_url}/messages/",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_current_weather",
                    "arguments": {
                        "location": location
                    }
                }
            },
            timeout=15.0
        )
        
        if response.status_code != 200:
            print(f"   ❌ Ошибка HTTP: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return False
        
        data = response.json()
        
        if "error" in data:
            print(f"   ❌ Ошибка MCP: {json.dumps(data['error'], indent=2, ensure_ascii=False)}")
            return False
        
        if "result" in data:
            content = data["result"].get("content", [])
            if content and len(content) > 0:
                weather_text = content[0].get("text", "")
                print(f"   ✅ Успешно получена погода:")
                print(f"   {'─' * 60}")
                # Выводим с отступами для читаемости
                for line in weather_text.split("\n"):
                    print(f"   {line}")
                print(f"   {'─' * 60}")
                return True
            else:
                print(f"   ⚠️  Пустой ответ")
                return False
        else:
            print(f"   ⚠️  Неожиданный формат ответа")
            print(f"   {json.dumps(data, indent=2, ensure_ascii=False)}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


async def test_forecast(client: httpx.AsyncClient, base_url: str, location: str = "Санкт-Петербург", days: int = 3) -> bool:
    """Тест получения прогноза погоды."""
    print(f"\n🔍 Тест 4: Получение прогноза погоды ({location}, {days} дней)")
    print(f"   POST {base_url}/messages/")
    try:
        response = await client.post(
            f"{base_url}/messages/",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_weather_forecast",
                    "arguments": {
                        "location": location,
                        "days": days
                    }
                }
            },
            timeout=15.0
        )
        
        if response.status_code != 200:
            print(f"   ❌ Ошибка HTTP: {response.status_code}")
            return False
        
        data = response.json()
        
        if "error" in data:
            print(f"   ❌ Ошибка MCP: {json.dumps(data['error'], indent=2, ensure_ascii=False)}")
            return False
        
        if "result" in data:
            content = data["result"].get("content", [])
            if content and len(content) > 0:
                forecast_text = content[0].get("text", "")
                print(f"   ✅ Успешно получен прогноз:")
                print(f"   {'─' * 60}")
                for line in forecast_text.split("\n")[:10]:  # Первые 10 строк
                    print(f"   {line}")
                if len(forecast_text.split("\n")) > 10:
                    print(f"   ... (показаны первые 10 строк)")
                print(f"   {'─' * 60}")
                return True
        return False
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


async def test_search_location(client: httpx.AsyncClient, base_url: str, city: str = "Новосибирск") -> bool:
    """Тест поиска местоположения."""
    print(f"\n🔍 Тест 5: Поиск местоположения ({city})")
    print(f"   POST {base_url}/messages/")
    try:
        response = await client.post(
            f"{base_url}/messages/",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "search_location",
                    "arguments": {
                        "city_name": city
                    }
                }
            },
            timeout=15.0
        )
        
        if response.status_code != 200:
            print(f"   ❌ Ошибка HTTP: {response.status_code}")
            return False
        
        data = response.json()
        
        if "error" in data:
            print(f"   ❌ Ошибка MCP: {json.dumps(data['error'], indent=2, ensure_ascii=False)}")
            return False
        
        if "result" in data:
            content = data["result"].get("content", [])
            if content and len(content) > 0:
                location_text = content[0].get("text", "")
                print(f"   ✅ Результат поиска:")
                print(f"   {location_text}")
                return True
        return False
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="Тестирование MCP Weather сервера")
    parser.add_argument("--host", default="localhost", help="Хост сервера (по умолчанию: localhost)")
    parser.add_argument("--port", type=int, default=9001, help="Порт сервера (по умолчанию: 9001)")
    parser.add_argument("--skip-forecast", action="store_true", help="Пропустить тест прогноза")
    parser.add_argument("--skip-search", action="store_true", help="Пропустить тест поиска")
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    
    print("=" * 70)
    print("🧪 Тестирование MCP Weather сервера")
    print("=" * 70)
    print(f"URL: {base_url}")
    print("=" * 70)
    print()
    
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Тест 1: Health check
        results.append(await test_health(client, base_url))
        
        # Тест 2: Список инструментов
        tools = await test_list_tools(client, base_url)
        results.append(tools is not None)
        
        # Тест 3: Текущая погода
        results.append(await test_get_weather(client, base_url))
        
        # Тест 4: Прогноз (опционально)
        if not args.skip_forecast:
            results.append(await test_forecast(client, base_url))
        
        # Тест 5: Поиск местоположения (опционально)
        if not args.skip_search:
            results.append(await test_search_location(client, base_url))
    
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
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
