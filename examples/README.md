# 📚 Примеры интеграции

Этот каталог содержит примеры интеграции MCP Weather с различными платформами и API.

## 📁 Файлы

- `deepseek_integration.py` - Пример интеграции с DeepSeek API через FastAPI

## 🚀 Быстрый старт

### 1. Убедитесь, что MCP Weather сервер запущен

```bash
# В корне проекта
python server_remote.py --host 0.0.0.0 --port 8001
```

### 2. Установите дополнительные зависимости для примеров

```bash
pip install fastapi uvicorn httpx
```

### 3. Запустите пример интеграции

```bash
# Установите переменные окружения
export MCP_WEATHER_URL="http://localhost:8001/sse"
export DEEPSEEK_API_KEY="your-api-key"

# Запустите сервер
uvicorn examples.deepseek_integration:app --host 0.0.0.0 --port 8000
```

### 4. Протестируйте endpoints

```bash
# Health check
curl http://localhost:8000/health

# Получить конфигурацию MCP
curl http://localhost:8000/api/mcp/config

# Получить погоду через прокси
curl "http://localhost:8000/api/weather/current?location=Москва"

# Чат с агентом
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Какая погода в Москве?", "use_weather_tools": true}'
```

## 📖 Документация

Подробная документация по интеграции с DeepSeek API находится в [DEEPSEEK_INTEGRATION.md](../DEEPSEEK_INTEGRATION.md).
