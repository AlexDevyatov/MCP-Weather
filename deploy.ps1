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
    
    $port = if ($env:SERVER_PORT) { $env:SERVER_PORT } else { "8000" }
    
    # Проверка порта
    $portInUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($portInUse) {
        Write-Warn "Порт $port уже занят. Используйте переменную SERVER_PORT для другого порта"
        Write-Warn "Например: `$env:SERVER_PORT=8001; .\deploy.ps1 docker"
        $continue = Read-Host "Продолжить с портом $port? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            exit 1
        }
    }
    
    Write-Info "Остановка существующих контейнеров..."
    docker-compose down 2>$null
    
    Write-Info "Сборка образа..."
    docker-compose build
    
    Write-Info "Запуск контейнера на порту $port..."
    $env:SERVER_PORT = $port
    docker-compose up -d
    
    Write-Info "Ожидание запуска сервера..."
    Start-Sleep -Seconds 3
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$port/health" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            Write-Info "✓ Сервер успешно запущен!"
            Write-Info "SSE endpoint: http://localhost:$port/sse"
            Write-Info "Health check: http://localhost:$port/health"
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
    
    $port = if ($env:SERVER_PORT) { $env:SERVER_PORT } else { "8000" }
    $host = if ($env:SERVER_HOST) { $env:SERVER_HOST } else { "0.0.0.0" }
    
    # Проверка порта
    $portInUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($portInUse) {
        Write-Warn "Порт $port уже занят. Используйте переменную SERVER_PORT для другого порта"
        Write-Warn "Например: `$env:SERVER_PORT=8001; .\deploy.ps1 direct"
        $continue = Read-Host "Продолжить с портом $port? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            exit 1
        }
    }
    
    Write-Info "Запуск server_remote.py на ${host}:${port}..."
    Write-Info "Для остановки нажмите Ctrl+C"
    Write-Info ""
    
    & "venv\Scripts\python.exe" server_remote.py --host $host --port $port
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
