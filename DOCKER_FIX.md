# 🔧 Исправление ошибки "container name already in use"

## Проблема

Ошибка: `The container name "/mcp-weather" is already in use`

## Решение

### Вариант 1: Удалить старый контейнер и пересобрать

```bash
# Остановите и удалите старый контейнер
docker stop mcp-weather
docker rm mcp-weather

# Или одной командой
docker rm -f mcp-weather

# Теперь пересоберите и запустите
docker compose up -d --build --force-recreate
```

### Вариант 2: Использовать docker compose (рекомендуется)

```bash
# Остановите и удалите старый контейнер
docker compose down

# Пересоберите и запустите
docker compose up -d --build --force-recreate
```

### Вариант 3: Если используете docker run напрямую

```bash
# Остановите и удалите старый контейнер
docker stop mcp-weather
docker rm mcp-weather

# Пересоберите образ
docker build -t mcp-weather --no-cache .

# Запустите новый контейнер
docker run -d --name mcp-weather --restart unless-stopped \
  -p 9001:9001 \
  -e SERVER_PORT=9001 \
  -e SERVER_HOST=0.0.0.0 \
  mcp-weather
```

## Проверка

После пересборки:

```bash
# Проверьте статус
docker ps | grep mcp-weather

# Проверьте логи
docker logs mcp-weather

# Health check
curl http://localhost:9001/health

# Тест
python test_mcp.py --port 9001
```

## Быстрая команда (все в одной)

```bash
docker compose down && docker compose up -d --build --force-recreate
```

Или для старой версии docker-compose:

```bash
docker-compose down && docker-compose up -d --build --force-recreate
```
