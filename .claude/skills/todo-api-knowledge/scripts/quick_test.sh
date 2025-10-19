#!/bin/bash
# Quick Smoke Test for TODO API
# シンプルで高速なスモークテスト（Bashスクリプト版）

set -e  # エラー時に停止

# カラーコード
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# デフォルト設定
API_URL="${TODO_API_URL:-http://localhost:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# オプション解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            API_URL="$2"
            shift 2
            ;;
        --host)
            API_HOST="$2"
            shift 2
            ;;
        --port)
            API_PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ホスト・ポートからURL構築
if [ -n "$API_HOST" ]; then
    API_PORT="${API_PORT:-8000}"
    API_URL="http://${API_HOST}:${API_PORT}"
fi

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}TODO API - Quick Smoke Test${NC}"
echo -e "${BLUE}=====================================${NC}"
echo -e "API URL: ${API_URL}\n"

# カウンター
PASSED=0
FAILED=0

# テスト関数
test_endpoint() {
    local test_name=$1
    local command=$2

    echo -e "${YELLOW}Testing: ${test_name}${NC}"

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ ${test_name} - PASSED${NC}\n"
        ((PASSED++))
    else
        echo -e "${RED}✗ ${test_name} - FAILED${NC}\n"
        ((FAILED++))
    fi
}

# Python API Client を使用したテスト
test_with_python() {
    local test_name=$1
    local command=$2

    echo -e "${YELLOW}Testing: ${test_name}${NC}"

    if python "$SCRIPT_DIR/api_client.py" --url "$API_URL" $command > /dev/null 2>&1; then
        echo -e "${GREEN}✓ ${test_name} - PASSED${NC}\n"
        ((PASSED++))
    else
        echo -e "${RED}✗ ${test_name} - FAILED${NC}\n"
        ((FAILED++))
    fi
}

# テスト実行

# 1. ヘルスチェック（curl）
echo -e "${BLUE}[1/5] Health Check (curl)${NC}"
test_endpoint "Health Check" "curl -s -f ${API_URL}/"

# 2. ヘルスチェック（Python Client）
echo -e "${BLUE}[2/5] Health Check (Python Client)${NC}"
test_with_python "Health Check via Python" "health_check"

# 3. タスク一覧取得
echo -e "${BLUE}[3/5] Get Tasks${NC}"
test_with_python "Get Tasks List" "get_tasks"

# 4. タスクツリー取得
echo -e "${BLUE}[4/5] Get Task Tree${NC}"
test_with_python "Get Task Tree" "get_task_tree"

# 5. APIドキュメント確認
echo -e "${BLUE}[5/5] API Documentation${NC}"
test_endpoint "API Docs Access" "curl -s -f ${API_URL}/docs"

# 結果表示
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}=====================================${NC}"
TOTAL=$((PASSED + FAILED))
echo -e "Total Tests:  ${TOTAL}"
echo -e "${GREEN}Passed:       ${PASSED}${NC}"
echo -e "${RED}Failed:       ${FAILED}${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}\n"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed${NC}\n"
    exit 1
fi
