# 🧪 Тестирование MCP Weather сервера через curl

## ✅ Быстрая проверка

### 1. Health Check (самый простой тест)

```bash
curl http://localhost:9001/health
```

**Ожидаемый результат:** `OK`

Если сервер работает, вы получите ответ `OK`.

---

## 🔌 Тестирование SSE endpoint

### 2. Подключение к SSE endpoint

SSE (Server-Sent Events) endpoint используется для подключения MCP клиентов:

```bash
curl -N http://localhost:9001/sse
```

**Что происходит:**
- `-N` отключает буферизацию, чтобы видеть события в реальном времени
- Подключение останется открытым и будет ждать событий

**Ожидаемое поведение:** Подключение установится, но событий может не быть до отправки MCP сообщений.

**Для остановки:** Нажмите `Ctrl+C`

---

## 📨 Тестирование MCP протокола

MCP работает через JSON-RPC сообщения. Вот как можно протестировать:

### 3. Инициализация MCP сессии

```bash
curl -X POST http://localhost:9001/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'
```

**Ожидаемый результат:** JSON ответ с информацией о сервере и доступных инструментах.

### 4. Получение списка инструментов

```bash
curl -X POST http://localhost:9001/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }'
```

**Ожидаемый результат:** Список доступных инструментов:
- `get_current_weather`
- `get_weather_forecast`
- `search_location`

### 5. Вызов инструмента: Текущая погода

```bash
curl -X POST http://localhost:9001/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "get_current_weather",
      "arguments": {
        "location": "Москва"
      }
    }
  }'
```

**Ожидаемый результат:** JSON с данными о текущей погоде в Москве.

### 6. Вызов инструмента: Прогноз погоды

```bash
curl -X POST http://localhost:9001/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "get_weather_forecast",
      "arguments": {
        "location": "Санкт-Петербург",
        "days": 3
      }
    }
  }'
```

### 7. Поиск местоположения

```bash
curl -X POST http://localhost:9001/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "tools/call",
    "params": {
      "name": "search_location",
      "arguments": {
        "city_name": "Новосибирск"
      }
    }
  }'
```

---

## 🐍 Альтернатива: Python скрипт для тестирования

Создайте файл `test_mcp.py`:

```python
#!/usr/bin/env python3
"""Простой скрипт для тестирования MCP Weather сервера."""
import asyncio
import httpx
import json

MCP_URL = "http://localhost:9001"

async def test_mcp():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health check
        print("1. Health check...")
        response = await client.get(f"{MCP_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}\n")
        
        # 2. Получение списка инструментов
        print("2. Получение списка инструментов...")
        response = await client.post(
            f"{MCP_URL}/messages/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
        )
        print(f"   Status: {response.status_code}")
        data = response.json()
        if "result" in data and "tools" in data["result"]:
            tools = data["result"]["tools"]
            print(f"   Найдено инструментов: {len(tools)}")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
        print()
        
        # 3. Вызов инструмента погоды
        print("3. Получение текущей погоды в Москве...")
        response = await client.post(
            f"{MCP_URL}/messages/",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_current_weather",
                    "arguments": {
                        "location": "Москва"
                    }
                }
            }
        )
        print(f"   Status: {response.status_code}")
        data = response.json()
        if "result" in data:
            content = data["result"].get("content", [])
            if content and len(content) > 0:
                print(f"   Результат:\n{content[0].get('text', '')}")
        print()

if __name__ == "__main__":
    asyncio.run(test_mcp())
```

Запуск:
```bash
pip install httpx
python test_mcp.py
```

---

## 🔍 Проверка через Docker

### Просмотр логов контейнера

```bash
docker logs mcp-weather
```

### Просмотр логов в реальном времени

```bash
docker logs -f mcp-weather
```

### Проверка статуса контейнера

```bash
docker ps | grep mcp-weather
```

### Проверка порта

```bash
docker port mcp-weather
```

---

## 📋 Чеклист тестирования

- [ ] Health check возвращает `OK`
- [ ] SSE endpoint доступен (подключение устанавливается)
- [ ] Можно получить список инструментов через `/messages/`
- [ ] Инструмент `get_current_weather` работает
- [ ] Инструмент `get_weather_forecast` работает
- [ ] Инструмент `search_location` работает

---

## 🐛 Решение проблем

### Ошибка "Connection refused"
```bash
# Проверьте, что контейнер запущен
docker ps | grep mcp-weather

# Проверьте порт
docker port mcp-weather
```

### Ошибка "Method not allowed"
- Убедитесь, что используете правильный HTTP метод (GET для `/health` и `/sse`, POST для `/messages/`)

### Ошибка "Invalid JSON"
- Проверьте формат JSON в запросе
- Убедитесь, что заголовок `Content-Type: application/json` установлен

### Нет ответа от инструментов
- Проверьте логи контейнера: `docker logs mcp-weather`
- Убедитесь, что есть интернет-соединение (для запросов к Open-Meteo API)

---

## 💡 Полезные команды

### Полный тест одним скриптом

```bash
#!/bin/bash
echo "=== Тестирование MCP Weather сервера ==="
echo ""
echo "1. Health check:"
curl -s http://localhost:9001/health
echo ""
echo ""
echo "2. Список инструментов:"
curl -s -X POST http://localhost:9001/messages/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | jq .
echo ""
echo "3. Текущая погода в Москве:"
curl -s -X POST http://localhost:9001/messages/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_current_weather","arguments":{"location":"Москва"}}}' | jq -r '.result.content[0].text'
```

Сохраните как `test.sh`, сделайте исполняемым и запустите:
```bash
chmod +x test.sh
./test.sh
```

**Примечание:** Для красивого вывода JSON установите `jq`: `brew install jq` (macOS) или `apt-get install jq` (Linux)
