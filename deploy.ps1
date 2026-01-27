# Скрипт автоматического развертывания MCP Weather Server для Windows
# Использование: .\deploy.ps1 [docker|direct]

param(
    [Parameter(Position=0)]
    [ValidateSet("docker", "direct")]
    [string]$Method = "direct"
)

$ErrorActionPreference = "Stop"

function Write-Info {
    Write-Host "[INFO] $args" -ForegroundColor Green
}

function Write-Warn {
    Write-Host "[WARN] $args" -ForegroundColor Yellow
}

function Write-Error {
    Write-Host "[ERROR] $args" -ForegroundColor Red
}

# Проверка Python
function Test-Python {
    try {
        $pythonVersion = python --version 2>&1
        Write-Info "Python версия: $pythonVersion"
        
        $version = [version]($pythonVersion -replace "Python ", "")
        if ($version.Major -lt 3 -or ($version.Major -eq 3 -and $version.Minor -lt 10)) {
            Write-Error "Требуется Python 3.10+, найдено: $version"
            exit 1
        }
    } catch {
        Write-Error "Python не найден. Установите Python 3.10+"
        exit 1
    }
}

# Создание виртуального окружения
function Setup-Venv {
    if (-not (Test-Path "venv")) {
        Write-Info "Создание виртуального окружения..."
        python -m venv venv
    } else {
        Write-Info "Виртуальное окружение уже существует"
    }
    
    Write-Info "Активация виртуального окружения..."
    & "venv\Scripts\Activate.ps1"
    
    Write-Info "Обновление pip..."
    python -m pip install --upgrade pip --quiet
    
    Write-Info "Установка зависимостей..."
    pip install -r requirements.txt --quiet
    
    Write-Info "Зависимости установлены"
}

# Развертывание через Docker
function Deploy-Docker {
    Write-Info "Развертывание через Docker..."
    
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker не найден. Установите Docker Desktop"
        exit 1
    }
    
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error "Docker Compose не найден. Установите Docker Compose"
        exit 1
    }
    
    Write-Info "Остановка существующих контейнеров..."
    docker-compose down 2>$null
    
    Write-Info "Сборка образа..."
    docker-compose build
    
    Write-Info "Запуск контейнера..."
    docker-compose up -d
    
    Write-Info "Ожидание запуска сервера..."
    Start-Sleep -Seconds 3
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            Write-Info "✓ Сервер успешно запущен!"
            Write-Info "SSE endpoint: http://localhost:8000/sse"
            Write-Info "Health check: http://localhost:8000/health"
            Write-Info ""
            Write-Info "Просмотр логов: docker-compose logs -f"
            Write-Info "Остановка: docker-compose down"
        }
    } catch {
        Write-Warn "Сервер запущен, но health check не прошел. Проверьте логи: docker-compose logs"
    }
}

# Прямой запуск
function Deploy-Direct {
    Write-Info "Прямой запуск сервера..."
    
    Setup-Venv
    
    Write-Info "Запуск server_remote.py..."
    Write-Info "Для остановки нажмите Ctrl+C"
    Write-Info ""
    
    & "venv\Scripts\python.exe" server_remote.py --host 0.0.0.0 --port 8000
}

# Основная функция
function Main {
    Write-Info "=== MCP Weather Server - Автоматическое развертывание ==="
    Write-Info ""
    
    switch ($Method) {
        "docker" {
            Test-Python
            Deploy-Docker
        }
        "direct" {
            Test-Python
            Setup-Venv
            Deploy-Direct
        }
        default {
            Write-Error "Неизвестный метод развертывания: $Method"
            Write-Host ""
            Write-Host "Использование: .\deploy.ps1 [docker|direct]"
            Write-Host ""
            Write-Host "Методы:"
            Write-Host "  docker   - Развертывание через Docker Compose"
            Write-Host "  direct   - Прямой запуск (по умолчанию)"
            exit 1
        }
    }
}

# Запуск
Main
