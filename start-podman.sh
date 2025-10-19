#!/bin/bash

# Podman用起動スクリプト
echo "🚀 Starting TODO API with Podman..."

# Podmanがインストールされているかチェック
if ! command -v podman &> /dev/null; then
    echo "❌ Podman is not installed. Please install Podman first."
    echo "   - RHEL/CentOS: sudo dnf install podman"
    echo "   - Ubuntu/Debian: sudo apt install podman"
    echo "   - macOS: brew install podman"
    exit 1
fi

# Podman Composeがインストールされているかチェック
if ! command -v podman-compose &> /dev/null; then
    echo "❌ podman-compose is not installed. Installing..."
    pip install podman-compose
fi

# 既存のコンテナを停止・削除
echo "🧹 Cleaning up existing containers..."
podman-compose -f podman-compose.yml down 2>/dev/null || true

# イメージをビルド
echo "🔨 Building images..."
podman-compose -f podman-compose.yml build

# サービスを起動
echo "🚀 Starting services..."
podman-compose -f podman-compose.yml up -d

# ヘルスチェック
echo "⏳ Waiting for services to be ready..."
sleep 10

# APIのヘルスチェック
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ TODO API is running at http://localhost:8000"
    echo "✅ Redis is running at localhost:6379"
    echo "✅ Celery Flower is running at http://localhost:5555"
    echo ""
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo "🌺 Celery Flower: http://localhost:5555"
else
    echo "❌ Failed to start services. Check logs with:"
    echo "   podman-compose -f podman-compose.yml logs"
fi
