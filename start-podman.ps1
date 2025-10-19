# Podman用起動スクリプト (PowerShell)
Write-Host "🚀 Starting TODO API with Podman..." -ForegroundColor Green

# Podmanがインストールされているかチェック
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Podman is not installed. Please install Podman first." -ForegroundColor Red
    Write-Host "   - Windows: Download from https://podman.io/getting-started/installation" -ForegroundColor Yellow
    Write-Host "   - Or use WSL2 with Podman" -ForegroundColor Yellow
    exit 1
}

# Podman Composeがインストールされているかチェック
if (-not (Get-Command podman-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ podman-compose is not installed. Installing..." -ForegroundColor Yellow
    pip install podman-compose
}

# 既存のコンテナを停止・削除
Write-Host "🧹 Cleaning up existing containers..." -ForegroundColor Yellow
podman-compose -f podman-compose.yml down 2>$null

# イメージをビルド
Write-Host "🔨 Building images..." -ForegroundColor Yellow
podman-compose -f podman-compose.yml build

# サービスを起動
Write-Host "🚀 Starting services..." -ForegroundColor Yellow
podman-compose -f podman-compose.yml up -d

# ヘルスチェック
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# APIのヘルスチェック
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ TODO API is running at http://localhost:8000" -ForegroundColor Green
        Write-Host "✅ Redis is running at localhost:6379" -ForegroundColor Green
        Write-Host "✅ Celery Flower is running at http://localhost:5555" -ForegroundColor Green
        Write-Host ""
        Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host "🌺 Celery Flower: http://localhost:5555" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Failed to start services. Check logs with:" -ForegroundColor Red
    Write-Host "   podman-compose -f podman-compose.yml logs" -ForegroundColor Yellow
}
