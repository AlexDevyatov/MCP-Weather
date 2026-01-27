# Подключение MCP Weather к AI-агенту

Этот MCP-сервер можно использовать с любым клиентом, поддерживающим [Model Context Protocol](https://modelcontextprotocol.io/): Cursor, Claude Desktop, другие IDE и кастомные агенты.

---

## 1. Cursor

### Вариант A: Workspace (уже настроено)

В проекте есть `.cursor/mcp.json`. Сервер подхватится автоматически, если:

1. Создано виртуальное окружение: `python3 -m venv venv`
2. Установлены зависимости: `pip install -r requirements.txt`
3. Cursor открыт в папке **MCPWeather** (как workspace)
4. Cursor перезапущен после первых настройках

Использование: `@weather get_current_weather location="Москва"` и т.п.

### Вариант B: Глобально (все проекты)

Чтобы погода была доступна в любом проекте:

1. Откройте глобальный MCP-конфиг Cursor:
   - **macOS/Linux:** `~/.cursor/mcp.json`
   - **Windows:** `%USERPROFILE%\.cursor\mcp.json`

2. Добавьте сервер (подставьте **полный путь** к вашему проекту):

```json
{
  "mcpServers": {
    "weather": {
      "command": "/ПУТЬ/К/MCPWeather/venv/bin/python",
      "args": ["/ПУТЬ/К/MCPWeather/server.py"],
      "cwd": "/ПУТЬ/К/MCPWeather",
      "env": {
        "DEFAULT_LANG": "ru",
        "DEFAULT_LOCATION": "55.75396,37.620393",
        "CACHE_TTL": "600",
        "LOG_LEVEL": "INFO",
        "REQUEST_TIMEOUT": "10"
      }
    }
  }
}
```

**Пример для macOS:** если проект в `/Users/alexdevyatov/PycharmProjects/MCPWeather`:

```json
"command": "/Users/alexdevyatov/PycharmProjects/MCPWeather/venv/bin/python",
"args": ["/Users/alexdevyatov/PycharmProjects/MCPWeather/server.py"],
"cwd": "/Users/alexdevyatov/PycharmProjects/MCPWeather",
```

3. Перезапустите Cursor.

---

## 2. Claude Desktop

1. Убедитесь, что в MCPWeather создано `venv` и установлены зависимости (`pip install -r requirements.txt`).

2. Откройте конфиг Claude Desktop:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

   Через приложение: **Claude → Settings… → Developer → Edit Config**.

3. Добавьте сервер в `mcpServers`. Если файл пустой или его нет:

```json
{
  "mcpServers": {
    "weather": {
      "command": "/ПУТЬ/К/MCPWeather/venv/bin/python",
      "args": ["/ПУТЬ/К/MCPWeather/server.py"],
      "cwd": "/ПУТЬ/К/MCPWeather",
      "env": {
        "DEFAULT_LANG": "ru",
        "DEFAULT_LOCATION": "55.75396,37.620393",
        "CACHE_TTL": "600",
        "LOG_LEVEL": "INFO",
        "REQUEST_TIMEOUT": "10"
      }
    }
  }
}
```

Подставьте вместо `/ПУТЬ/К/MCPWeather` реальный путь к проекту.

4. Полностью закройте Claude Desktop и запустите снова.

5. В чате нажмите «+» → **Connectors** и убедитесь, что отображается **weather** и его инструменты.

---

## 3. Другие MCP-клиенты

Сервер работает через **stdio**: клиент запускает процесс и общается с ним по stdin/stdout по протоколу MCP.

- **Command:** путь к Python из `venv`: `.../MCPWeather/venv/bin/python` (или `python.exe` на Windows).
- **Args:** `server.py` (полный путь: `.../MCPWeather/server.py`).
- **Cwd:** корень проекта `.../MCPWeather`.

Переменные окружения опциональны; без них используются значения по умолчанию (см. `config.py` и `.env.example`).

---

## Доступные инструменты для агента

| Инструмент | Описание |
|------------|----------|
| `get_current_weather` | Текущая погода (город или координаты) |
| `get_weather_forecast` | Прогноз на 1–7 дней |
| `search_location` | Поиск координат по названию города |

Подробнее — в [README.md](README.md).

---

## Проверка подключения

**Ручной запуск сервера** (убедитесь, что он вообще стартует):

```bash
cd /ПУТЬ/К/MCPWeather
source venv/bin/activate   # Windows: venv\Scripts\activate
python server.py
```

Сервер ждёт ввод по stdio. Завершите процесс (Ctrl+C) и настройте агента как выше.

**Логи:**

- **Cursor:** вывод MCP-серверов в панели Cursor.
- **Claude Desktop:** `~/Library/Logs/Claude/mcp*.log` (macOS), `%APPDATA%\Claude\logs` (Windows).

---

## Частые проблемы

- **«Сервер не появляется»** — проверьте пути в конфиге (должны быть абсолютными), наличие `venv` и `pip install -r requirements.txt`, перезапуск приложения.
- **«Requires Python 3.10+»** — создайте `venv` с Python 3.10+ и укажите в `command` именно этот интерпретатор.
- **Ошибки API** — проверьте интернет; Open-Meteo не требует API-ключа.

Дополнительно: [QUICKSTART.md](QUICKSTART.md), [SETUP.md](SETUP.md).
