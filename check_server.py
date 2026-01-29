#!/usr/bin/env python3
"""Проверка доступности API (порт 8000) и MCP-сервера погоды (порт 9001).

Использование:
    python3 check_server.py

Проверяет:
- http://localhost:8000/api/health — dev-сервер (если используется)
- http://localhost:9001/health — MCP-сервер погоды (или URL из MCP_WEATHER_SERVER_URL в .env)
"""
import os
import sys
import urllib.request
import urllib.error

# Попытка загрузить URL из .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
MCP_URL = os.environ.get("MCP_WEATHER_SERVER_URL", "http://127.0.0.1:9001")


def check(url: str, timeout: int = 3) -> bool:
    """Проверяет доступность URL. Возвращает True при HTTP 2xx."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= r.status < 300
    except (urllib.error.URLError, OSError) as e:
        print(f"  Ошибка: {e}")
        return False


def main() -> int:
    print("Проверка доступности серверов\n")
    ok = True

    api_health = f"{API_BASE.rstrip('/')}/api/health"
    print(f"1. API (dev): {api_health}")
    if check(api_health):
        print("   OK\n")
    else:
        print("   Недоступен\n")
        ok = False

    mcp_health = f"{MCP_URL.rstrip('/')}/health"
    print(f"2. MCP-погода: {mcp_health}")
    if check(mcp_health):
        print("   OK\n")
    else:
        print("   Недоступен\n")
        ok = False

    if not ok:
        print("Итог: один или оба сервера недоступны.")
        print("Для «Чата о погоде» запустите MCP на 9001:")
        print("  python3 server_remote.py --host 0.0.0.0 --port 9001")
        print("Или укажите в .env: MCP_WEATHER_SERVER_URL=http://127.0.0.1:9001")
        return 1
    print("Итог: оба сервера доступны.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
