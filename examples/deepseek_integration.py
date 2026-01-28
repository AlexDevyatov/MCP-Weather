"""
Пример интеграции MCP Weather с DeepSeek API.

Этот файл демонстрирует различные способы подключения MCP Weather сервера
к вашему веб-приложению с DeepSeek API агентом.
"""
import os
import asyncio
import httpx
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Конфигурация
MCP_WEATHER_URL = os.getenv("MCP_WEATHER_URL", "http://localhost:8001/sse")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Запрос на чат с агентом."""
    message: str
    use_weather_tools: bool = True


class WeatherRequest(BaseModel):
    """Запрос на получение погоды."""
    location: str
    days: Optional[int] = None


# ============================================================================
# Способ 1: Прямая интеграция через MCP Client
# ============================================================================

async def get_weather_via_mcp_client(location: str) -> Dict[str, Any]:
    """
    Получение погоды через MCP клиент.
    
    Требует установки: pip install mcp
    """
    try:
        from mcp import ClientSession
        from mcp.client.sse import sse_client
        
        async with sse_client(MCP_WEATHER_URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "get_current_weather",
                    {"location": location}
                )
                
                return {
                    "success": True,
                    "data": result.content[0].text if result.content else "Нет данных"
                }
    except ImportError:
        return {
            "success": False,
            "error": "MCP client не установлен. Установите: pip install mcp"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# Способ 2: Проксирование через ваш API
# ============================================================================

@app.get("/api/weather/current")
async def get_current_weather_proxy(location: str):
    """
    Прокси endpoint для получения текущей погоды.
    Используйте этот endpoint в вашем DeepSeek API агенте.
    """
    result = await get_weather_via_mcp_client(location)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return {
        "location": location,
        "weather": result["data"]
    }


@app.get("/api/weather/forecast")
async def get_weather_forecast_proxy(location: str, days: int = 3):
    """
    Прокси endpoint для получения прогноза погоды.
    """
    # Аналогично get_current_weather_proxy, но с другим инструментом
    return {
        "location": location,
        "days": days,
        "mcp_tool": "get_weather_forecast",
        "mcp_url": MCP_WEATHER_URL
    }


# ============================================================================
# Способ 3: Интеграция с DeepSeek API через Function Calling
# ============================================================================

def get_weather_function_definition() -> Dict[str, Any]:
    """
    Определение функции для DeepSeek API Function Calling.
    
    DeepSeek API поддерживает function calling, где вы можете определить
    функции, которые агент может вызывать. Здесь мы определяем функцию,
    которая будет проксировать запросы к MCP серверу.
    """
    return {
        "name": "get_current_weather",
        "description": "Получение текущей погоды для указанного местоположения",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Название города или координаты в формате 'lat,lon'"
                }
            },
            "required": ["location"]
        }
    }


async def execute_weather_function(location: str) -> str:
    """
    Выполнение функции погоды для DeepSeek API.
    
    Эта функция вызывается, когда DeepSeek API решает использовать
    функцию get_current_weather.
    """
    result = await get_weather_via_mcp_client(location)
    
    if result["success"]:
        return result["data"]
    else:
        return f"Ошибка получения погоды: {result.get('error')}"


@app.post("/api/chat")
async def chat_with_deepseek(request: ChatRequest):
    """
    Чат с DeepSeek API агентом с поддержкой MCP Weather инструментов.
    
    Пример использования:
    POST /api/chat
    {
        "message": "Какая погода в Москве?",
        "use_weather_tools": true
    }
    """
    # Здесь вы интегрируетесь с DeepSeek API
    # Пример структуры запроса (точный формат зависит от вашей библиотеки):
    
    functions = []
    if request.use_weather_tools:
        functions.append(get_weather_function_definition())
    
    # Пример вызова DeepSeek API (замените на реальный код):
    """
    import openai  # или ваша библиотека DeepSeek
    
    client = openai.OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"  # или ваш endpoint
    )
    
    messages = [
        {
            "role": "system",
            "content": "Ты полезный ассистент с доступом к инструментам погоды."
        },
        {
            "role": "user",
            "content": request.message
        }
    ]
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        functions=functions if functions else None,
        function_call="auto" if functions else None
    )
    
    # Обработка function calls
    if response.choices[0].message.function_call:
        function_name = response.choices[0].message.function_call.name
        function_args = json.loads(response.choices[0].message.function_call.arguments)
        
        if function_name == "get_current_weather":
            function_result = await execute_weather_function(function_args["location"])
            # Продолжить диалог с результатом функции
    """
    
    # Временный ответ для демонстрации
    return {
        "message": request.message,
        "mcp_enabled": request.use_weather_tools,
        "mcp_url": MCP_WEATHER_URL,
        "available_functions": [f["name"] for f in functions] if functions else [],
        "note": "Замените этот код на реальную интеграцию с DeepSeek API"
    }


# ============================================================================
# Способ 4: Конфигурация MCP для DeepSeek API
# ============================================================================

@app.get("/api/mcp/config")
async def get_mcp_config():
    """
    Получить конфигурацию MCP сервера для DeepSeek API.
    
    DeepSeek API может поддерживать прямое подключение к MCP серверам
    через SSE. Используйте эту конфигурацию в настройках вашего агента.
    """
    return {
        "mcpServers": {
            "weather": {
                "url": MCP_WEATHER_URL,
                "name": "weather",
                "description": "MCP сервер для получения данных о погоде",
                "tools": [
                    {
                        "name": "get_current_weather",
                        "description": "Получение текущей погоды для указанного местоположения",
                        "parameters": {
                            "location": {
                                "type": "string",
                                "description": "Название города или координаты"
                            }
                        }
                    },
                    {
                        "name": "get_weather_forecast",
                        "description": "Получение прогноза погоды на несколько дней",
                        "parameters": {
                            "location": {"type": "string"},
                            "days": {"type": "integer", "default": 3}
                        }
                    },
                    {
                        "name": "search_location",
                        "description": "Поиск координат по названию города",
                        "parameters": {
                            "city_name": {"type": "string"}
                        }
                    }
                ]
            }
        }
    }


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Проверка здоровья API и MCP сервера."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Проверяем доступность MCP сервера
            response = await client.get(MCP_WEATHER_URL.replace("/sse", "/health"))
            mcp_status = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        mcp_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "mcp_weather": {
            "url": MCP_WEATHER_URL,
            "status": mcp_status
        }
    }


# ============================================================================
# Пример использования
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print(f"""
    🌤️  MCP Weather Integration Server
    
    MCP Weather URL: {MCP_WEATHER_URL}
    
    Доступные endpoints:
    - GET  /health                    - Проверка здоровья
    - GET  /api/mcp/config            - Конфигурация MCP для DeepSeek API
    - GET  /api/weather/current       - Прокси для текущей погоды
    - GET  /api/weather/forecast      - Прокси для прогноза
    - POST /api/chat                  - Чат с DeepSeek API агентом
    
    Запуск:
    uvicorn examples.deepseek_integration:app --host 0.0.0.0 --port 8000
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
