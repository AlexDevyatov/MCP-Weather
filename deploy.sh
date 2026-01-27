#!/bin/bash

# Скрипт автоматического развертывания MCP Weather Server
# Использование: ./deploy.sh [docker|systemd|direct]

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия Python
check_python() {
    if ! command -v python3 &> /dev/null; then
        error "Python 3 не найден. Установите Python 3.10+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    REQUIRED_VERSION="3.10"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        error "Требуется Python 3.10+, найдено: $PYTHON_VERSION"
        exit 1
    fi
    
    info "Python версия: $(python3 --version)"
}

# Создание виртуального окружения
setup_venv() {
    if [ ! -d "venv" ]; then
        info "Создание виртуального окружения..."
        python3 -m venv venv
    else
        info "Виртуальное окружение уже существует"
    fi
    
    info "Активация виртуального окружения..."
    source venv/bin/activate
    
    info "Обновление pip..."
    pip install --upgrade pip --quiet
    
    info "Установка зависимостей..."
    pip install -r requirements.txt --quiet
    
    info "Зависимости установлены"
}

# Развертывание через Docker
deploy_docker() {
    info "Развертывание через Docker..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker не найден. Установите Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose не найден. Установите Docker Compose"
        exit 1
    fi
    
    info "Остановка существующих контейнеров..."
    docker-compose down 2>/dev/null || true
    
    info "Сборка образа..."
    docker-compose build
    
    info "Запуск контейнера..."
    docker-compose up -d
    
    info "Ожидание запуска сервера..."
    sleep 3
    
    if curl -s http://localhost:8000/health > /dev/null; then
        info "✓ Сервер успешно запущен!"
        info "SSE endpoint: http://localhost:8000/sse"
        info "Health check: http://localhost:8000/health"
        info ""
        info "Просмотр логов: docker-compose logs -f"
        info "Остановка: docker-compose down"
    else
        warn "Сервер запущен, но health check не прошел. Проверьте логи: docker-compose logs"
    fi
}

# Развертывание через systemd
deploy_systemd() {
    info "Развертывание через systemd..."
    
    if [ "$EUID" -ne 0 ]; then
        error "Для systemd требуется запуск от root (sudo)"
        exit 1
    fi
    
    # Получаем абсолютный путь к проекту
    PROJECT_DIR=$(pwd)
    USER=$(logname 2>/dev/null || echo $SUDO_USER || echo $USER)
    
    info "Проект: $PROJECT_DIR"
    info "Пользователь: $USER"
    
    # Создаем файл сервиса
    SERVICE_FILE="/etc/systemd/system/mcp-weather.service"
    
    info "Создание systemd сервиса..."
    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=MCP Weather Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python server_remote.py --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    info "Перезагрузка systemd..."
    systemctl daemon-reload
    
    info "Включение автозапуска..."
    systemctl enable mcp-weather
    
    info "Запуск сервиса..."
    systemctl start mcp-weather
    
    sleep 2
    
    if systemctl is-active --quiet mcp-weather; then
        info "✓ Сервис успешно запущен!"
        info "SSE endpoint: http://localhost:8000/sse"
        info ""
        info "Управление:"
        info "  Статус: sudo systemctl status mcp-weather"
        info "  Логи: sudo journalctl -u mcp-weather -f"
        info "  Остановка: sudo systemctl stop mcp-weather"
        info "  Перезапуск: sudo systemctl restart mcp-weather"
    else
        error "Сервис не запустился. Проверьте логи: sudo journalctl -u mcp-weather"
        exit 1
    fi
}

# Прямой запуск
deploy_direct() {
    info "Прямой запуск сервера..."
    
    setup_venv
    
    info "Запуск server_remote.py..."
    info "Для остановки нажмите Ctrl+C"
    info ""
    
    source venv/bin/activate
    python server_remote.py --host 0.0.0.0 --port 8000
}

# Основная функция
main() {
    info "=== MCP Weather Server - Автоматическое развертывание ==="
    info ""
    
    DEPLOY_METHOD=${1:-direct}
    
    case $DEPLOY_METHOD in
        docker)
            check_python
            deploy_docker
            ;;
        systemd)
            check_python
            setup_venv
            deploy_systemd
            ;;
        direct)
            check_python
            setup_venv
            deploy_direct
            ;;
        *)
            error "Неизвестный метод развертывания: $DEPLOY_METHOD"
            echo ""
            echo "Использование: $0 [docker|systemd|direct]"
            echo ""
            echo "Методы:"
            echo "  docker   - Развертывание через Docker Compose"
            echo "  systemd  - Развертывание как systemd сервис (требует sudo)"
            echo "  direct   - Прямой запуск (по умолчанию)"
            exit 1
            ;;
    esac
}

# Запуск
main "$@"
