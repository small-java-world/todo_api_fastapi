# Quick Smoke Test for TODO API (PowerShell版)
# シンプルで高速なスモークテスト（Windows PowerShell）

param(
    [string]$Url = "",
    [string]$Host = "",
    [string]$Port = ""
)

# デフォルト設定
$ApiUrl = if ($Url) { $Url } elseif ($env:TODO_API_URL) { $env:TODO_API_URL } else { "http://localhost:8000" }

# ホスト・ポートからURL構築
if ($Host) {
    $ApiPort = if ($Port) { $Port } else { "8000" }
    $ApiUrl = "http://${Host}:${ApiPort}"
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=====================================" -ForegroundColor Blue
Write-Host "TODO API - Quick Smoke Test" -ForegroundColor Blue
Write-Host "=====================================" -ForegroundColor Blue
Write-Host "API URL: $ApiUrl`n"

# カウンター
$Passed = 0
$Failed = 0

# テスト関数
function Test-Endpoint {
    param(
        [string]$TestName,
        [scriptblock]$TestCommand
    )

    Write-Host "Testing: $TestName" -ForegroundColor Yellow

    try {
        $null = & $TestCommand
        Write-Host "✓ $TestName - PASSED`n" -ForegroundColor Green
        $script:Passed++
    }
    catch {
        Write-Host "✗ $TestName - FAILED`n" -ForegroundColor Red
        $script:Failed++
    }
}

# Python API Client を使用したテスト
function Test-WithPython {
    param(
        [string]$TestName,
        [string]$Command
    )

    Write-Host "Testing: $TestName" -ForegroundColor Yellow

    try {
        $output = python "$ScriptDir\api_client.py" --url $ApiUrl $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ $TestName - PASSED`n" -ForegroundColor Green
            $script:Passed++
        }
        else {
            Write-Host "✗ $TestName - FAILED`n" -ForegroundColor Red
            $script:Failed++
        }
    }
    catch {
        Write-Host "✗ $TestName - FAILED`n" -ForegroundColor Red
        $script:Failed++
    }
}

# テスト実行

# 1. ヘルスチェック（PowerShell）
Write-Host "[1/5] Health Check (HTTP Request)" -ForegroundColor Blue
Test-Endpoint "Health Check" {
    $response = Invoke-RestMethod -Uri "$ApiUrl/" -Method Get -ErrorAction Stop
    if (-not $response.message) {
        throw "No message in response"
    }
}

# 2. ヘルスチェック（Python Client）
Write-Host "[2/5] Health Check (Python Client)" -ForegroundColor Blue
Test-WithPython "Health Check via Python" "health_check"

# 3. タスク一覧取得
Write-Host "[3/5] Get Tasks" -ForegroundColor Blue
Test-WithPython "Get Tasks List" "get_tasks"

# 4. タスクツリー取得
Write-Host "[4/5] Get Task Tree" -ForegroundColor Blue
Test-WithPython "Get Task Tree" "get_task_tree"

# 5. APIドキュメント確認
Write-Host "[5/5] API Documentation" -ForegroundColor Blue
Test-Endpoint "API Docs Access" {
    $response = Invoke-WebRequest -Uri "$ApiUrl/docs" -Method Get -ErrorAction Stop
    if ($response.StatusCode -ne 200) {
        throw "Status code is not 200"
    }
}

# 結果表示
Write-Host "=====================================" -ForegroundColor Blue
Write-Host "Test Summary" -ForegroundColor Blue
Write-Host "=====================================" -ForegroundColor Blue
$Total = $Passed + $Failed
Write-Host "Total Tests:  $Total"
Write-Host "Passed:       $Passed" -ForegroundColor Green
Write-Host "Failed:       $Failed" -ForegroundColor Red

if ($Failed -eq 0) {
    Write-Host "`n✓ All tests passed!`n" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "`n✗ Some tests failed`n" -ForegroundColor Red
    exit 1
}
