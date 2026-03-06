# ============================================================================
# QA 环境启动脚本
# ============================================================================

param(
    [switch]$Build,
    [switch]$Clean
)

. "$PSScriptRoot\utils.ps1"

Write-Step "Starting FastAPI QA Environment"

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

Write-Info "Starting QA environment..."
docker compose -f docker-compose.yml -f docker-compose-qa.yml up -d

if ($LASTEXITCODE -eq 0) {
    Write-Success "QA environment started successfully!"
    Write-Info ""
    Write-Info "📊 Services Status:"
    docker compose ps
    Write-Info ""
    Write-Info "🔗 API: http://localhost:8000/docs"
} else {
    Exit-WithError "Failed to start QA environment"
}
