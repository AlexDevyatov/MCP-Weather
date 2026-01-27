# ⚡ Быстрый старт: Развертывание на удаленном сервере

## 🚀 Автоматическое развертывание (рекомендуется)

### Linux/macOS:
```bash
# Прямой запуск
./deploy.sh direct

# Docker
./deploy.sh docker

# Systemd (требует sudo)
sudo ./deploy.sh systemd
```

### Windows:
```powershell
# Прямой запуск
.\deploy.ps1 direct

# Docker
.\deploy.ps1 docker
```

## 🐳 Docker (самый простой способ)

```bash
# 1. Клонируйте проект на сервер
git clone <your-repo> MCPWeather
cd MCPWeather

# 2. Запустите через Docker Compose
docker-compose up -d

# 3. Проверьте статус
docker-compose ps
curl http://localhost:8000/health
```

Сервер будет доступен на `http://your-server:8000/sse`

## 🔧 Systemd (Linux)

```bash
# 1. Создайте сервис
sudo nano /etc/systemd/system/mcp-weather.service
```

Вставьте (замените пути):
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

[Install]
WantedBy=multi-user.target
```

```bash
# 2. Запустите
sudo systemctl enable mcp-weather
sudo systemctl start mcp-weather
sudo systemctl status mcp-weather
```

## 🔌 Подключение клиента

В конфиге вашего MCP-клиента (Cursor, Claude Desktop и т.д.):

```json
{
  "mcpServers": {
    "weather": {
      "url": "http://your-server:8000/sse"
    }
  }
}
```

## 🔒 Безопасность (рекомендуется)

1. **Настройте firewall:**
   ```bash
   sudo ufw allow from YOUR_IP to any port 8000
   ```

2. **Используйте Nginx с HTTPS** (см. [DEPLOYMENT.md](DEPLOYMENT.md))

## 📚 Полная документация

См. [DEPLOYMENT.md](DEPLOYMENT.md) для детальных инструкций по:
- Настройке Nginx reverse proxy
- SSL/HTTPS конфигурации
- Мониторингу и логированию
- Решению проблем
