# ⚡ Быстрый старт: Интеграция с DeepSeek API

## 🎯 Цель

Подключить MCP Weather сервер к вашему сайту с агентом DeepSeek API.

## 📋 Шаг 1: Запуск MCP Weather сервера

### На вашем сервере:

```bash
cd /path/to/MCPWeather

# Убедитесь, что зависимости установлены
source venv/bin/activate
pip install -r requirements.txt

# Запустите удаленный сервер (порт 8001)
python server_remote.py --host 0.0.0.0 --port 8001
```

**Важно:** Используйте порт, который не конфликтует с вашим веб-сайтом!

### Или через Docker:

```bash
docker-compose up -d
```

### Проверка:

```bash
curl http://localhost:8001/health
# Должен вернуть: OK
```

## 🔗 Шаг 2: Получите URL MCP сервера

Ваш MCP сервер будет доступен по адресу:

```
http://your-server-ip:8001/sse
```

Если используете домен и Nginx, настройте проксирование (см. [DEEPSEEK_INTEGRATION.md](DEEPSEEK_INTEGRATION.md)).

## 🤖 Шаг 3: Интеграция с DeepSeek API

### Вариант A: Прямое подключение (если DeepSeek API поддерживает MCP)

В конфигурации вашего DeepSeek API агента добавьте:

```json
{
  "mcpServers": {
    "weather": {
      "url": "http://your-server:8001/sse"
    }
  }
}
```

### Вариант B: Через прокси API (рекомендуется)

Используйте пример из `examples/deepseek_integration.py`:

```bash
# Установите зависимости
pip install fastapi uvicorn httpx

# Запустите прокси сервер
export MCP_WEATHER_URL="http://localhost:8001/sse"
export DEEPSEEK_API_KEY="your-api-key"
uvicorn examples.deepseek_integration:app --host 0.0.0.0 --port 8000
```

Теперь используйте endpoints:
- `GET /api/weather/current?location=Москва` - текущая погода
- `GET /api/mcp/config` - конфигурация MCP для DeepSeek API
- `POST /api/chat` - чат с поддержкой погоды

## 📝 Пример использования в коде

```python
import httpx

async def get_weather(location: str):
    """Получение погоды через MCP прокси."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/weather/current",
            params={"location": location}
        )
        return response.json()
```

## 🔧 Настройка для production

1. **Используйте HTTPS** для MCP сервера
2. **Настройте Nginx** для проксирования (см. [DEEPSEEK_INTEGRATION.md](DEEPSEEK_INTEGRATION.md))
3. **Ограничьте доступ** через firewall
4. **Используйте systemd** для автозапуска (см. [DEPLOYMENT.md](DEPLOYMENT.md))

## 📚 Подробная документация

- [DEEPSEEK_INTEGRATION.md](DEEPSEEK_INTEGRATION.md) - полное руководство по интеграции
- [examples/deepseek_integration.py](examples/deepseek_integration.py) - пример кода
- [DEPLOYMENT.md](DEPLOYMENT.md) - развертывание на сервере

## 🐛 Решение проблем

### Порт занят
```bash
# Используйте другой порт
python server_remote.py --host 0.0.0.0 --port 8002
```

### Сервер не доступен
- Проверьте firewall: `sudo ufw status`
- Убедитесь, что слушает на `0.0.0.0`, а не `127.0.0.1`
- Проверьте логи: `journalctl -u mcp-weather -f` (для systemd)

---

**Готово! Теперь ваш DeepSeek API агент может использовать инструменты погоды! 🌤️**
