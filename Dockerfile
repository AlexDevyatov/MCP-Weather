FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей (если нужны)
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Открываем порт
EXPOSE 8001

# Переменные окружения по умолчанию
ENV DEFAULT_LANG=ru
ENV LOG_LEVEL=INFO
ENV CACHE_TTL=600
ENV REQUEST_TIMEOUT=10
ENV SERVER_PORT=8001
ENV SERVER_HOST=185.28.85.26

# Health check (использует переменную SERVER_PORT)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os, urllib.request; port=os.getenv('SERVER_PORT', '8001'); urllib.request.urlopen(f'http://localhost:{port}/health')" || exit 1

# Запускаем сервер (порт берется из переменной окружения)
CMD python server_remote.py --host ${SERVER_HOST} --port ${SERVER_PORT}
