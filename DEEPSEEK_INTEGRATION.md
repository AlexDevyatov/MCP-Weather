# 🔌 Интеграция MCP Weather с DeepSeek API

Это руководство поможет вам подключить MCP Weather сервер к вашему сайту с агентом DeepSeek API.

## 📋 Обзор

MCP Weather сервер работает через **SSE (Server-Sent Events)** транспорт, что позволяет подключать его к DeepSeek API через HTTP endpoint. Сервер предоставляет три инструмента:
- `get_current_weather` - текущая погода
- `get_weather_forecast` - прогноз на несколько дней
- `search_location` - поиск координат города

## 🚀 Шаг 1: Развертывание MCP Weather сервера

### Вариант A: На том же сервере, где ваш сайт

```bash
# 1. Перейдите в директорию проекта
cd /path/to/MCPWeather

# 2. Убедитесь, что виртуальное окружение создано и зависимости установлены
source venv/bin/activate
pip install -r requirements.txt

# 3. Запустите удаленный сервер (по умолчанию порт 8001)
python server_remote.py --host 0.0.0.0 --port 8001

# Или на другом порту, если 8001 занят
python server_remote.py --host 0.0.0.0 --port 8002
```

**Важно:** Используйте порт, который не конфликтует с вашим веб-сайтом!

### Вариант B: Через Docker (рекомендуется)

```bash
# 1. Отредактируйте docker-compose.yml, если нужно изменить порт
# По умолчанию используется порт 8001

# 2. Запустите контейнер
docker-compose up -d

# 3. Проверьте статус
docker-compose ps
curl http://localhost:8001/health
```

### Вариант C: Через Systemd (Linux)

Создайте файл `/etc/systemd/system/mcp-weather.service`:

```ini
[Unit]
Description=MCP Weather Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/MCPWeather
Environment="PATH=/path/to/MCPWeather/venv/bin"
ExecStart=/path/to/MCPWeather/venv/bin/python server_remote.py --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запустите:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-weather
sudo systemctl start mcp-weather
```

## 🔗 Шаг 2: Настройка Nginx (если используется)

Если ваш сайт работает через Nginx, добавьте проксирование для MCP сервера:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Ваш основной сайт
    location / {
        # ... ваши настройки
    }

    # MCP Weather сервер
    location /mcp-weather/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Таймауты для SSE
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffering off;
    }
}
```

После этого MCP сервер будет доступен по адресу: `http://your-domain.com/mcp-weather/sse`

## 🤖 Шаг 3: Интеграция с DeepSeek API

### Способ 1: Через MCP Client SDK (Python)

Установите MCP клиент:

```bash
pip install mcp
```

Пример кода для подключения к MCP серверу:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client

async def main():
    # URL вашего MCP сервера
    mcp_url = "http://your-server:8001/sse"
    # Или если через Nginx: "http://your-domain.com/mcp-weather/sse"
    
    async with sse_client(mcp_url) as (read, write):
        async with ClientSession(read, write) as session:
            # Инициализация
            await session.initialize()
            
            # Получение списка инструментов
            tools = await session.list_tools()
            print("Доступные инструменты:", [t.name for t in tools.tools])
            
            # Использование инструмента
            result = await session.call_tool(
                "get_current_weather",
                {"location": "Москва"}
            )
            print("Результат:", result.content)

if __name__ == "__main__":
    asyncio.run(main())
```

### Способ 2: Прямое использование через HTTP API

Если DeepSeek API поддерживает прямую интеграцию с MCP через SSE:

```python
import httpx
import json

async def get_weather_via_mcp(location: str):
    """
    Получение погоды через MCP сервер для использования с DeepSeek API.
    """
    # URL вашего MCP сервера
    mcp_base_url = "http://your-server:8001"
    
    # DeepSeek API может использовать MCP через SSE endpoint
    # Обычно это делается через конфигурацию агента
    
    # Для прямого вызова инструмента (если поддерживается):
    async with httpx.AsyncClient() as client:
        # Это пример - точный формат зависит от вашей реализации DeepSeek API
        response = await client.post(
            f"{mcp_base_url}/messages/",
            json={
                "method": "tools/call",
                "params": {
                    "name": "get_current_weather",
                    "arguments": {"location": location}
                }
            }
        )
        return response.json()
```

### Способ 3: Интеграция в веб-приложение (Flask/FastAPI)

Пример для FastAPI:

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL вашего MCP сервера
MCP_SERVER_URL = "http://localhost:8001"

@app.post("/api/weather/current")
async def get_current_weather(location: str):
    """
    Прокси для получения текущей погоды через MCP сервер.
    Используйте этот endpoint в вашем DeepSeek API агенте.
    """
    try:
        # Здесь вы можете использовать MCP клиент или делать прямые HTTP запросы
        # В зависимости от того, как DeepSeek API интегрируется с MCP
        
        # Пример: если DeepSeek API поддерживает MCP через SSE
        # Вы можете передать URL MCP сервера в конфигурацию DeepSeek API
        
        return {
            "mcp_server_url": f"{MCP_SERVER_URL}/sse",
            "tool": "get_current_weather",
            "arguments": {"location": location}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/weather/forecast")
async def get_weather_forecast(location: str, days: int = 3):
    """Прокси для получения прогноза погоды."""
    return {
        "mcp_server_url": f"{MCP_SERVER_URL}/sse",
        "tool": "get_weather_forecast",
        "arguments": {"location": location, "days": days}
    }
```

## 🔧 Шаг 4: Конфигурация DeepSeek API

DeepSeek API поддерживает MCP серверы через SSE транспорт. В конфигурации вашего DeepSeek API агента добавьте:

### JSON конфигурация (если поддерживается):

```json
{
  "mcpServers": {
    "weather": {
      "url": "http://your-server:8001/sse"
    }
  }
}
```

### Или через переменные окружения:

```bash
export DEEPSEEK_MCP_WEATHER_URL="http://your-server:8001/sse"
```

### Пример для Python агента:

```python
# В вашем коде DeepSeek API агента
from deepseek import DeepSeek

# Настройка MCP сервера
mcp_config = {
    "weather": {
        "url": "http://your-server:8001/sse"
    }
}

# Инициализация агента с MCP
agent = DeepSeek(
    api_key="your-api-key",
    mcp_servers=mcp_config
)

# Теперь агент может использовать инструменты погоды
response = agent.chat(
    "Какая погода в Москве?",
    tools=["weather.get_current_weather"]  # Использование MCP инструмента
)
```

## 🧪 Шаг 5: Тестирование

### 1. Проверьте, что MCP сервер запущен:

```bash
curl http://localhost:8001/health
# Должен вернуть: OK
```

### 2. Проверьте SSE endpoint:

```bash
curl http://localhost:8001/sse
# Должен начать поток SSE событий
```

### 3. Проверьте список инструментов:

```python
import httpx

async def test_mcp():
    async with httpx.AsyncClient() as client:
        # Это зависит от реализации вашего MCP сервера
        # Обычно MCP работает через SSE, а не прямые HTTP запросы
        pass

# Лучше использовать MCP клиент для тестирования
```

## 📝 Пример полной интеграции

Вот пример того, как можно интегрировать MCP Weather в ваш веб-приложение с DeepSeek API:

```python
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os

app = FastAPI()

# Конфигурация
MCP_WEATHER_URL = os.getenv("MCP_WEATHER_URL", "http://localhost:8001/sse")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

class ChatRequest(BaseModel):
    message: str
    use_weather: bool = True

@app.post("/chat")
async def chat_with_agent(request: ChatRequest):
    """
    Чат с DeepSeek API агентом, использующим MCP Weather.
    """
    # Если запрос связан с погодой, используем MCP инструменты
    if request.use_weather and any(word in request.message.lower() 
                                    for word in ["погода", "weather", "температура"]):
        
        # DeepSeek API с MCP конфигурацией
        # Это пример - точный синтаксис зависит от вашей библиотеки DeepSeek
        system_prompt = f"""
        У тебя есть доступ к инструментам погоды через MCP сервер.
        MCP сервер доступен по адресу: {MCP_WEATHER_URL}
        
        Доступные инструменты:
        - get_current_weather: получение текущей погоды
        - get_weather_forecast: прогноз на несколько дней
        - search_location: поиск координат города
        
        Используй эти инструменты для ответа на вопросы о погоде.
        """
        
        # Здесь вы вызываете DeepSeek API с MCP конфигурацией
        # response = deepseek_client.chat(
        #     message=request.message,
        #     system=system_prompt,
        #     mcp_servers={"weather": {"url": MCP_WEATHER_URL}}
        # )
        
        return {
            "response": "Используйте MCP инструменты для получения погоды",
            "mcp_enabled": True,
            "mcp_url": MCP_WEATHER_URL
        }
    
    # Обычный чат без MCP
    # response = deepseek_client.chat(message=request.message)
    return {"response": "Обычный ответ"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 🔒 Безопасность

1. **Firewall:** Ограничьте доступ к MCP серверу только с вашего веб-сервера:
   ```bash
   sudo ufw allow from YOUR_WEB_SERVER_IP to any port 8001
   ```

2. **HTTPS:** Используйте HTTPS для MCP сервера в production:
   ```nginx
   # В Nginx конфигурации
   location /mcp-weather/ {
       proxy_pass https://127.0.0.1:8001/;
       # ... остальные настройки
   }
   ```

3. **Аутентификация:** Добавьте базовую аутентификацию, если MCP сервер доступен извне.

## 🐛 Решение проблем

### MCP сервер не запускается
- Проверьте, что порт не занят: `lsof -i :8001`
- Используйте другой порт: `python server_remote.py --port 8002`
- Проверьте логи: `journalctl -u mcp-weather -f` (для systemd)

### DeepSeek API не видит инструменты
- Убедитесь, что URL правильный: `http://your-server:8001/sse`
- Проверьте доступность: `curl http://your-server:8001/health`
- Проверьте формат конфигурации MCP в DeepSeek API

### Ошибки подключения
- Проверьте firewall: `sudo ufw status`
- Проверьте, что сервер слушает на правильном интерфейсе: `0.0.0.0`, а не `127.0.0.1`
- Проверьте логи Nginx, если используете прокси

## 📚 Дополнительные ресурсы

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [DeepSeek API Documentation](https://platform.deepseek.com/docs)
- [DEPLOYMENT.md](DEPLOYMENT.md) - подробное руководство по развертыванию
- [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) - быстрый старт

---

**Готово! Теперь ваш DeepSeek API агент может использовать инструменты погоды через MCP сервер! 🌤️**
