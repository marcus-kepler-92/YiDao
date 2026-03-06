# ============================================================================
# 生产环境启动脚本
# ============================================================================

param(
    [switch]$Build,
    [switch]$Clean
)

. "$PSScriptRoot\utils.ps1"

Write-Step "Starting FastAPI Production Environment"

if (-not (Test-Docker)) {
    Exit-WithError "Please install Docker Desktop"
}

if ($Clean) {
    Write-CustomWarning "Cleaning up old containers..."
    docker compose down
}

if ($Build) {
    Write-Info "Building Docker images..."
    docker compose build --no-cache
}

Write-Info "Starting production environment (detached mode)..."
docker compose -f docker-compose.yml -f docker-compose-prod.yml up -d

if ($LASTEXITCODE -eq 0) {
    Write-Success "Production environment started successfully!"
    Write-Info ""
    Write-Info "📊 Services Status:"
    docker compose ps
    Write-Info ""
    Write-Info "📋 View logs:"
    Write-Info "  docker compose logs -f web"
    Write-Info "  docker compose logs -f db"
    Write-Info "  docker compose logs -f redis"
} else {
    Exit-WithError "Failed to start production environment"
}
