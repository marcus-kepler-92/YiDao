# ============================================================================
# Restart services script
# ============================================================================

param(
    [Parameter(Position=0)]
    [ValidateSet("dev", "qa", "prod")]
    [string]$Env = "dev",

    [string]$Service
)

. "$PSScriptRoot\utils.ps1"

$composeFile = switch ($Env) {
    "dev"  { "docker-compose-dev.yml" }
    "qa"   { "docker-compose-qa.yml" }
    "prod" { "docker-compose-prod.yml" }
}

if ($Service) {
    Write-Step "Restarting service '$Service' in $Env environment..."
    docker compose -f docker-compose.yml -f $composeFile restart $Service
} else {
    Write-Step "Restarting all services in $Env environment..."
    docker compose -f docker-compose.yml -f $composeFile restart
}

if ($LASTEXITCODE -eq 0) {
    Write-Success "Restart completed!"
    docker compose ps
} else {
    Exit-WithError "Failed to restart services"
}
