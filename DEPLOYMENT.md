# 🚀 Развертывание MCP Weather на удаленном сервере

Этот документ описывает, как развернуть MCP Weather сервер на удаленном сервере для доступа через HTTP/SSE.

## 📋 Варианты развертывания

### Вариант 1: Прямой запуск (для тестирования)

```bash
# На сервере
cd /path/to/MCPWeather
source venv/bin/activate
python server_remote.py --host 0.0.0.0 --port 8000
```

Сервер будет доступен по адресу: `http://your-server:8000/sse`

### Вариант 2: Systemd Service (рекомендуется для Linux)

1. **Создайте файл сервиса** `/etc/systemd/system/mcp-weather.service`:

```ini
[Unit]
Description=MCP Weather Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/MCPWeather
Environment="PATH=/path/to/MCPWeather/venv/bin"
ExecStart=/path/to/MCPWeather/venv/bin/python server_remote.py --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. **Активируйте и запустите сервис:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-weather
sudo systemctl start mcp-weather
sudo systemctl status mcp-weather
```

3. **Просмотр логов:**

```bash
sudo journalctl -u mcp-weather -f
```

### Вариант 3: Docker

1. **Создайте `Dockerfile`:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Открываем порт
EXPOSE 8000

# Запускаем сервер
CMD ["python", "server_remote.py", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Создайте `.dockerignore`:**

```
venv/
__pycache__/
*.pyc
.env
.git/
.gitignore
```

3. **Соберите и запустите контейнер:**

```bash
docker build -t mcp-weather .
docker run -d -p 8000:8000 --name mcp-weather --restart unless-stopped mcp-weather
```

4. **Или используйте `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  mcp-weather:
    build: .
    ports:
      - "8000:8000"
    restart: unless-stopped
    environment:
      - DEFAULT_LANG=ru
      - LOG_LEVEL=INFO
      - CACHE_TTL=600
```

Запуск: `docker-compose up -d`

### Вариант 4: Nginx Reverse Proxy (для production)

1. **Настройте Nginx** `/etc/nginx/sites-available/mcp-weather`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
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
    }
}
```

2. **Активируйте конфигурацию:**

```bash
sudo ln -s /etc/nginx/sites-available/mcp-weather /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

3. **SSL через Let's Encrypt (опционально):**

```bash
sudo certbot --nginx -d your-domain.com
```

## 🔧 Подключение клиента к удаленному серверу

### Cursor

В `.cursor/mcp.json` или глобальном конфиге:

```json
{
  "mcpServers": {
    "weather": {
      "url": "http://your-server:8000/sse"
    }
  }
}
```

### Claude Desktop

В `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "weather": {
      "url": "http://your-server:8000/sse"
    }
  }
}
```

### Другие MCP-клиенты

Используйте SSE endpoint: `http://your-server:8000/sse`

## 🔒 Безопасность

### 1. Firewall

```bash
# Разрешить только определенные IP
sudo ufw allow from YOUR_IP to any port 8000
```

### 2. Аутентификация (опционально)

Добавьте базовую аутентификацию через Nginx:

```nginx
location / {
    auth_basic "MCP Weather";
    auth_basic_user_file /etc/nginx/.htpasswd;
    # ... остальные настройки
}
```

Создание пользователя:
```bash
sudo htpasswd -c /etc/nginx/.htpasswd username
```

### 3. HTTPS

Всегда используйте HTTPS в production:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # ... остальные настройки
}
```

## 📊 Мониторинг

### Health Check Endpoint

Добавьте простой health check в `server_remote.py`:

```python
@starlette_app.route("/health")
async def health():
    return Response("OK", status_code=200)
```

### Логирование

Логи доступны через:
- Systemd: `journalctl -u mcp-weather`
- Docker: `docker logs mcp-weather`
- Файл: настройте в `logging.basicConfig()`

## 🐛 Решение проблем

### Сервер не запускается

1. Проверьте порт: `netstat -tulpn | grep 8000`
2. Проверьте логи: `journalctl -u mcp-weather -n 50`
3. Проверьте Python версию: `python --version` (должна быть 3.10+)

### Ошибки подключения

1. Проверьте firewall: `sudo ufw status`
2. Проверьте доступность: `curl http://your-server:8000/sse`
3. Проверьте логи Nginx: `sudo tail -f /var/log/nginx/error.log`

### Высокая нагрузка

1. Увеличьте количество workers: `--workers 4`
2. Используйте Nginx для балансировки
3. Настройте кэширование (уже встроено, TTL настраивается)

## 📝 Примеры конфигурации

### Production настройки

```bash
# server_remote.py с несколькими workers
python server_remote.py --host 0.0.0.0 --port 8000 --workers 4

# Или через systemd
ExecStart=/path/to/venv/bin/python server_remote.py --host 0.0.0.0 --port 8000 --workers 4
```

### Переменные окружения

Создайте `.env` на сервере:

```env
DEFAULT_LANG=ru
LOG_LEVEL=INFO
CACHE_TTL=600
REQUEST_TIMEOUT=10
```

## 🔗 Полезные ссылки

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Open-Meteo API](https://open-meteo.com/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
