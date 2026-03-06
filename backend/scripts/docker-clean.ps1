# ============================================================================
# 清理所有容器和卷
# ============================================================================

. "$PSScriptRoot\utils.ps1"

Write-CustomWarning "This will remove all containers and volumes!"
$confirm = Read-Host "Are you sure? (yes/no)"

if ($confirm -ne "yes") {
    Write-Info "Cleanup cancelled"
    exit 0
}

Write-Step "Cleaning up containers and volumes..."
docker compose down -v
docker system prune -f --volumes

if ($LASTEXITCODE -eq 0) {
    Write-Success "Cleanup completed successfully"
} else {
    Write-Error "Cleanup encountered some issues"
}
