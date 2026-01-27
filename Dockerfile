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
EXPOSE 8000

# Переменные окружения по умолчанию
ENV DEFAULT_LANG=ru
ENV LOG_LEVEL=INFO
ENV CACHE_TTL=600
ENV REQUEST_TIMEOUT=10

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Запускаем сервер
CMD ["python", "server_remote.py", "--host", "0.0.0.0", "--port", "8000"]
