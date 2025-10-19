# Podman用停止スクリプト (PowerShell)
Write-Host "🛑 Stopping TODO API with Podman..." -ForegroundColor Yellow

# サービスを停止
podman-compose -f podman-compose.yml down

Write-Host "✅ All services stopped." -ForegroundColor Green
