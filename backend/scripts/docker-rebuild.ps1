# ============================================================================
# Rebuild and restart services script
# ============================================================================

param(
    [Parameter(Position=0)]
    [ValidateSet("dev", "qa", "prod")]
    [string]$Env = "dev",

    [string]$Service,
    [switch]$NoCache
)

. "$PSScriptRoot\utils.ps1"

$composeFile = switch ($Env) {
    "dev"  { "docker-compose-dev.yml" }
    "qa"   { "docker-compose-qa.yml" }
    "prod" { "docker-compose-prod.yml" }
}

Write-Step "Rebuilding in $Env environment..."

if (-not (Test-Docker)) {
    Exit-WithError "Docker is not running"
}

$buildArgs = @("-f", "docker-compose.yml", "-f", $composeFile, "build")

if ($NoCache) {
    $buildArgs += "--no-cache"
    Write-Info "Building without cache..."
}

if ($Service) {
    $buildArgs += $Service
    Write-Info "Rebuilding service: $Service"
} else {
    Write-Info "Rebuilding all services..."
}

docker compose @buildArgs

if ($LASTEXITCODE -ne 0) {
    Exit-WithError "Build failed"
}

Write-Info "Restarting services..."

if ($Service) {
    docker compose -f docker-compose.yml -f $composeFile up -d $Service
} else {
    if ($Env -eq "dev") {
        docker compose -f docker-compose.yml -f $composeFile watch
    } else {
        docker compose -f docker-compose.yml -f $composeFile up -d
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Success "Rebuild completed!"
    docker compose ps
} else {
    Exit-WithError "Failed to start services after rebuild"
}
