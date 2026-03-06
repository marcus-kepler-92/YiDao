# ============================================================================
# 停止所有服务
# ============================================================================

. "$PSScriptRoot\utils.ps1"

Write-Step "Stopping all services..."
docker compose down

if ($LASTEXITCODE -eq 0) {
    Write-Success "All services stopped successfully"
} else {
    Write-Error "Failed to stop services"
}
