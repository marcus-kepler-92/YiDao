# Celery 集成测试快速启动脚本
# 用法: .\scripts\test-celery.ps1

# 导入工具函数
. "$PSScriptRoot\utils.ps1"

Write-ColorOutput "=" "Yellow" -NoNewline
Write-ColorOutput "=" "Yellow" -Repeat 49
Write-ColorOutput "Celery 集成测试" "Cyan"
Write-ColorOutput "=" "Yellow" -NoNewline
Write-ColorOutput "=" "Yellow" -Repeat 49

# 1. 检查 Docker
Write-ColorOutput "`n[1/6] 检查 Docker..." "Yellow"
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-ColorOutput "✗ Docker 未安装" "Red"
    exit 1
}
Write-ColorOutput "✓ Docker 已安装" "Green"

# 2. 启动基础服务
Write-ColorOutput "`n[2/6] 启动基础服务 (PostgreSQL, Redis)..." "Yellow"
docker compose up -d db redis

if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "✗ 基础服务启动失败" "Red"
    exit 1
}

Write-ColorOutput "等待服务就绪..." "Gray"
Start-Sleep -Seconds 5
Write-ColorOutput "✓ 基础服务已启动" "Green"

# 3. 运行数据库迁移
Write-ColorOutput "`n[3/6] 运行数据库迁移..." "Yellow"
uv run alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "⚠ 数据库迁移失败（可能已是最新）" "Yellow"
} else {
    Write-ColorOutput "✓ 数据库迁移完成" "Green"
}

# 4. 询问是否启动 Jaeger
Write-ColorOutput "`n[4/6] 是否启动 Jaeger 用于查看追踪? (y/n)" "Yellow"
$startJaeger = Read-Host

if ($startJaeger -eq "y" -or $startJaeger -eq "Y") {
    Write-ColorOutput "启动 Jaeger..." "Gray"

    # 检查是否已存在 jaeger 容器
    $jaegerExists = docker ps -a --filter "name=jaeger" --format "{{.Names}}"

    if ($jaegerExists) {
        Write-ColorOutput "Jaeger 容器已存在，正在启动..." "Gray"
        docker start jaeger | Out-Null
    } else {
        docker run -d --name jaeger `
            -p 5775:5775/udp `
            -p 6831:6831/udp `
            -p 6832:6832/udp `
            -p 5778:5778 `
            -p 16686:16686 `
            -p 14250:14250 `
            -p 14268:14268 `
            -p 14269:14269 `
            -p 9411:9411 `
            jaegertracing/all-in-one:latest | Out-Null
    }

    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✓ Jaeger 已启动: http://localhost:16686" "Green"
    } else {
        Write-ColorOutput "⚠ Jaeger 启动失败，继续测试" "Yellow"
    }
} else {
    Write-ColorOutput "跳过 Jaeger 启动" "Gray"
}

# 5. 启动 Celery Worker (在后台)
Write-ColorOutput "`n[5/6] 启动 Celery Worker..." "Yellow"
Write-ColorOutput "这将在新窗口中启动 Celery Worker" "Gray"

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD'; uv run celery -A app.tasks worker --loglevel=info"
)

Write-ColorOutput "✓ Celery Worker 已在新窗口中启动" "Green"
Write-ColorOutput "等待 Worker 初始化..." "Gray"
Start-Sleep -Seconds 5

# 6. 运行测试
Write-ColorOutput "`n[6/6] 运行集成测试..." "Yellow"
Write-ColorOutput "=" "Yellow" -NoNewline
Write-ColorOutput "=" "Yellow" -Repeat 49

uv run python test_celery_integration.py

$testExitCode = $LASTEXITCODE

# 测试结果
Write-ColorOutput "`n" "White"
Write-ColorOutput "=" "Yellow" -NoNewline
Write-ColorOutput "=" "Yellow" -Repeat 49

if ($testExitCode -eq 0) {
    Write-ColorOutput "✓ 测试通过!" "Green"
    Write-ColorOutput "`n接下来可以:" "Cyan"
    Write-ColorOutput "  • 访问 FastAPI 文档: http://localhost:8000/docs" "White"
    Write-ColorOutput "  • 查看 Prometheus 指标: http://localhost:8000/metrics" "White"

    if ($startJaeger -eq "y" -or $startJaeger -eq "Y") {
        Write-ColorOutput "  • 查看 Jaeger 追踪: http://localhost:16686" "White"
    }

    Write-ColorOutput "`n查看数据库审计日志:" "Cyan"
    Write-ColorOutput "  docker exec -it fastapi-template-db-1 psql -U postgres -d fastapi -c 'SELECT * FROM audit_log;'" "Gray"
} else {
    Write-ColorOutput "✗ 测试失败，请检查错误信息" "Red"
}

Write-ColorOutput "`n清理服务:" "Cyan"
Write-ColorOutput "  .\scripts\docker-down.ps1    # 停止所有服务" "White"
Write-ColorOutput "  .\scripts\docker-clean.ps1   # 清理所有数据" "White"

Write-ColorOutput "`n按任意键退出..." "Gray"
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
