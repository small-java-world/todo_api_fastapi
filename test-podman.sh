#!/bin/bash

# Podman用テスト実行スクリプト
echo "🧪 Running tests with Podman..."

# サービスが起動しているかチェック
if ! podman-compose -f podman-compose.yml ps | grep -q "todo-api.*Up"; then
    echo "❌ Services are not running. Please start them first:"
    echo "   ./start-podman.sh"
    exit 1
fi

# テスト実行
echo "🔨 Running unit tests..."
podman-compose -f podman-compose.yml exec todo-api python -m pytest tests/test_git_service_ut.py tests/test_config_ut.py tests/test_hierarchical_id_service_ut.py -v

echo "🔨 Running integration tests..."
podman-compose -f podman-compose.yml exec todo-api python -m pytest tests/test_integration.py tests/test_database_integration.py -v

echo "🔨 Running review service tests..."
podman-compose -f podman-compose.yml exec todo-api python -m pytest tests/test_review_service_ut.py -v

echo "🔨 Running backup service tests..."
podman-compose -f podman-compose.yml exec todo-api python -m pytest tests/test_backup_service_ut.py -v

echo "🔨 Running type check..."
podman-compose -f podman-compose.yml exec todo-api python -m mypy app/ --ignore-missing-imports --explicit-package-bases

echo "🔨 Running import order check..."
podman-compose -f podman-compose.yml exec todo-api python -m isort --check-only app/ --settings-path pyproject.toml

echo "✅ All tests completed!"
