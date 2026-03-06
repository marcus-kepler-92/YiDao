# ============================================================================
# 公共工具函数库
# ============================================================================

# 颜色定义
$Colors = @{
    Green = 'Green'
    Yellow = 'Yellow'
    Red = 'Red'
    Cyan = 'Cyan'
    Magenta = 'Magenta'
}

# 打印信息
function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor $Colors.Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $Colors.Green
}

function Write-CustomWarning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $Colors.Yellow
}

function Write-CustomError {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $Colors.Red
}

function Write-Step {
    param([string]$Message)
    Write-Host "🚀 $Message" -ForegroundColor $Colors.Magenta
}

# 检查 Docker 是否安装
function Test-Docker {
    try {
        $null = docker --version
        Write-Success "Docker is installed"
        return $true
    }
    catch {
        Write-CustomError "Docker is not installed or not in PATH"
        return $false
    }
}

# 检查容器是否运行
function Test-ServiceRunning {
    param([string]$ServiceName)
    $running = docker compose ps $ServiceName --format "{{.State}}" 2>$null
    return $running -eq "running"
}

# 等待服务就绪
function Wait-ServiceReady {
    param(
        [string]$ServiceName,
        [int]$MaxWaitSeconds = 60
    )
    
    $elapsed = 0
    while ($elapsed -lt $MaxWaitSeconds) {
        if (Test-ServiceRunning $ServiceName) {
            Write-Success "$ServiceName is ready"
            return $true
        }
        Write-Host "⏳ Waiting for $ServiceName... ($elapsed/$MaxWaitSeconds)" -ForegroundColor $Colors.Yellow
        Start-Sleep -Seconds 2
        $elapsed += 2
    }
    
    Write-CustomError "$ServiceName failed to start within $MaxWaitSeconds seconds"
    return $false
}

# 清理并退出
function Exit-WithError {
    param([string]$Message)
    Write-CustomError $Message
    exit 1
}

# 彩色输出函数（支持重复和不换行）
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White",
        [switch]$NoNewline,
        [int]$Repeat = 1
    )

    $text = $Message * $Repeat

    if ($NoNewline) {
        Write-Host $text -ForegroundColor $Color -NoNewline
    } else {
        Write-Host $text -ForegroundColor $Color
    }
}
