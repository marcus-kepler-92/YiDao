
# ============================================================================
# 查看服务日志
# ============================================================================

param(
    [string]$Service = "web",
    [int]$Tail = 50,
    [switch]$Follow
)

. "$PSScriptRoot\utils.ps1"

$LogService = $Service.ToLower()

Write-Info "Viewing logs for '$LogService' (last $Tail lines)..."
Write-Host ""

if ($Follow) {
    docker compose -f docker-compose.yml -f docker-compose-monitoring.yml logs -f --tail $Tail $LogService
} else {
    docker compose -f docker-compose.yml -f docker-compose-monitoring.yml logs --tail $Tail $LogService
}
