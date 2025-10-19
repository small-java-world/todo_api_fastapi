#!/bin/bash

# Podman用停止スクリプト
echo "🛑 Stopping TODO API with Podman..."

# サービスを停止
podman-compose -f podman-compose.yml down

echo "✅ All services stopped."
