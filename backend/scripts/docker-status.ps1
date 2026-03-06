# ============================================================================
# Show container status and health
# ============================================================================

. "$PSScriptRoot\utils.ps1"

Write-Step "Container Status"
Write-Host ""

docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

Write-Host ""
Write-Info "Resource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
