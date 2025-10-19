# Podman用テスト実行スクリプト (PowerShell)
Write-Host "🧪 Running tests with Podman..." -ForegroundColor Green

# サービスが起動しているかチェック
$services = podman-compose -f podman-compose.yml ps
if (-not ($services -match "todo-api.*Up")) {
    Write-Host "❌ Services are not running. Please start them first:" -ForegroundColor Red
    Write-Host "   .\start-podman.ps1" -ForegroundColor Yellow
    exit 1
}

# テスト実行
Write-Host "🔨 Running unit tests..." -ForegroundColor Yellow
podman-compose -f podman-compose.yml exec todo-api python -m pytest tests/test_git_service_ut.py tests/test_config_ut.py tests/test_hierarchical_id_service_ut.py -v

Write-Host "🔨 Running integration tests..." -ForegroundColor Yellow
podman-compose -f podman-compose.yml exec todo-api python -m pytest tests/test_integration.py tests/test_database_integration.py -v

Write-Host "🔨 Running review service tests..." -ForegroundColor Yellow
podman-compose -f podman-compose.yml exec todo-api python -m pytest tests/test_review_service_ut.py -v

Write-Host "🔨 Running backup service tests..." -ForegroundColor Yellow
podman-compose -f podman-compose.yml exec todo-api python -m pytest tests/test_backup_service_ut.py -v

Write-Host "🔨 Running type check..." -ForegroundColor Yellow
podman-compose -f podman-compose.yml exec todo-api python -m mypy app/ --ignore-missing-imports --explicit-package-bases

Write-Host "🔨 Running import order check..." -ForegroundColor Yellow
podman-compose -f podman-compose.yml exec todo-api python -m isort --check-only app/ --settings-path pyproject.toml

Write-Host "✅ All tests completed!" -ForegroundColor Green
