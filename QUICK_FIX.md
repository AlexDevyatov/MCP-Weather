# ⚡ Быстрое исправление ошибки валидации

## Проблема

Ошибка: `inputSchema Field required` при тестировании через SSE.

## Причина

Docker контейнер использует старый код с `input_schema` вместо `inputSchema`.

## Решение: Пересоберите Docker образ

Выполните на сервере, где запущен Docker:

```bash
cd /path/to/MCPWeather

# Остановите контейнер
docker compose down
# или если старая версия: docker-compose down

# Пересоберите образ БЕЗ кэша (важно!)
docker compose build --no-cache
# или: docker-compose build --no-cache

# Запустите заново
docker compose up -d
# или: docker-compose up -d

# Проверьте, что работает
curl http://localhost:9001/health
```

Или одной командой:

```bash
# Новая версия Docker (docker compose)
docker compose up -d --build --force-recreate

# Старая версия (docker-compose)
docker-compose up -d --build --force-recreate
```

## Проверка

После пересборки запустите тест:

```bash
python test_mcp.py --port 9001
```

Теперь все должно работать! ✅

## Почему это важно?

Docker кэширует слои при сборке. Если вы изменили Python код, но не пересобрали образ, контейнер будет использовать старый код из кэша. Флаг `--no-cache` гарантирует полную пересборку.
