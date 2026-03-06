# ============================================================================
# 开发环境启动脚本
# ============================================================================

param(
    [switch]$Build,
    [switch]$Clean
)

# 导入公共函数
. "$PSScriptRoot\utils.ps1"

Write-Step "Starting FastAPI Development Environment"

# 检查 Docker
if (-not (Test-Docker)) {
    Exit-WithError "Please install Docker Desktop"
}

# 清理旧容器（可选）
if ($Clean) {
    Write-CustomWarning "Cleaning up old containers..."
    docker compose down
    Start-Sleep -Seconds 2
}

# 构建镜像（可选）
if ($Build) {
    Write-Info "Building Docker images..."
    docker compose build --no-cache
}

# 启动开发环境
Write-Info "Starting services with hot-reload enabled..."
Write-Info "Press Ctrl+C to stop"
Write-Host ""

docker compose -f docker-compose.yml -f docker-compose-dev.yml watch

Write-Host ""
Write-CustomWarning "Development environment stopped"
