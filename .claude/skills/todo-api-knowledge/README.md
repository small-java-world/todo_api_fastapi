# TODO API Knowledge Skill

Claude Code用のTODO API知識ベーススキル

## 📋 概要

このスキルは、階層構造を持つTODO管理APIプロジェクトに関する包括的な知識をClaude Codeに提供します。コンテキストウィンドウを効率的に使用しながら、プロジェクトに関する正確な情報を自動的に取得できます。

### なぜこのスキルが必要か？

**問題**: 大規模プロジェクトでは、API仕様や設計パターンを繰り返し説明する必要があり、コンテキストウィンドウを大量に消費します。

**解決**: このスキルを使用することで、必要な情報のみを遅延ロードし、コンテキストを約**90%削減**できます。

### MCPサーバーとの違い

| 方式 | 初期ロード | コンテキスト消費 | 効率 |
|------|-----------|----------------|------|
| **MCP** | 全データ | 大（全データ読み込み） | ❌ |
| **Claude Skills** | メタデータのみ | 小（必要な情報のみ） | ✅ |

---

## 🚀 クイックスタート

### 1. Claude Codeを再起動

Skillを認識させるために、Claude Codeを再起動してください。

### 2. 自動認識（推奨）

再起動後、以下のような質問をするだけで自動的にSkillが動作します：

```
✅ 「階層IDの生成方法は?」
✅ 「要件を作成するAPIは?」
✅ 「レビューワークフローを教えて」
✅ 「バックアップの方法は?」
✅ 「TDDのベストプラクティスは?」
```

### 3. API呼び出し

APIを直接呼び出すこともできます：

```bash
# ヘルスチェック
python scripts/api_client.py health_check

# タスク一覧
python scripts/api_client.py get_tasks

# 要件作成
python scripts/api_client.py create_requirement "新要件" "説明"
```

---

## 📁 ファイル構成

```
todo-api-knowledge/
├── SKILL.md                    # メインのSkill定義ファイル（17KB）
├── README.md                   # このファイル
├── API_CLIENT_USAGE.md         # API Client詳細ガイド（7.3KB）
├── SMOKE_TEST_GUIDE.md         # スモークテストガイド（11KB）
├── config.json                 # 環境別設定（427B）
├── scripts/
│   ├── api_client.py          # API Clientライブラリ（16KB）
│   ├── smoke_test.py          # 完全版スモークテスト
│   ├── quick_test.sh          # 高速テスト（Linux/macOS）
│   └── quick_test.ps1         # 高速テスト（Windows）
└── resources/
    └── api_examples.json      # API使用例（8.6KB）
```

---

## 💡 主な機能

### 1. プロジェクト知識の提供

#### API仕様
- 階層構造管理（要件・タスク・サブタスク）
- レビュー管理
- バックアップ・復元
- アーティファクト管理
- Git統合
- CAS (Content-Addressable Storage)

#### アーキテクチャ
- FastAPI + SQLAlchemy + Celery
- 階層ID管理システム
- レビューワークフロー
- バックアップ戦略

#### ベストプラクティス
- TDD実装フロー
- レビュー管理
- エラーハンドリング
- パフォーマンス最適化

### 2. API接続管理

複数の方法でホスト名・ポートを指定可能：

```bash
# 方法1: コマンドライン引数
python scripts/api_client.py --url http://192.168.1.100:9000 health_check

# 方法2: 環境変数
export TODO_API_URL="http://192.168.1.100:9000"
python scripts/api_client.py health_check

# 方法3: 設定ファイル
python scripts/api_client.py --env production health_check
```

詳細は [`API_CLIENT_USAGE.md`](API_CLIENT_USAGE.md) を参照。

### 3. スモークテスト

3つのスモークテストを提供：

| スクリプト | プラットフォーム | テスト項目 | 実行時間 |
|-----------|----------------|----------|---------|
| **smoke_test.py** | Python（全OS） | 9項目 | 30-60秒 |
| **quick_test.sh** | Linux/macOS | 5項目 | 5-10秒 |
| **quick_test.ps1** | Windows | 5項目 | 5-10秒 |

```bash
# 完全版スモークテスト
python scripts/smoke_test.py

# 高速版（Linux/macOS）
bash scripts/quick_test.sh

# 高速版（Windows）
.\scripts\quick_test.ps1
```

詳細は [`SMOKE_TEST_GUIDE.md`](SMOKE_TEST_GUIDE.md) を参照。

---

## 🎯 使用例

### 例1: API仕様の確認

```
ユーザー: 「レビュー作成APIの使い方を教えて」

Claude Code: [Skillから情報を自動取得]
「レビュー作成APIは POST /reviews/ です。
以下のようにリクエストします:
{
  "target_type": "requirement",
  "target_id": 1,
  "review_type": "requirement_review",
  ...
}」
```

### 例2: 実際のデータ取得

```
ユーザー: 「現在のタスク一覧を取得して」

Claude Code: [スクリプト実行]
python scripts/api_client.py get_tasks
→ 結果を表示
```

### 例3: ワークフロー実行

```
ユーザー: 「新しい要件とタスクを作成して」

Claude Code: [Skillのワークフロー情報を参照]
1. 要件作成APIを呼び出し
2. 返されたIDを使ってタスク作成APIを呼び出し
3. 結果を報告
```

---

## ⚙️ API接続設定

### ホスト名・ポートの指定方法（優先順位順）

1. **コマンドライン引数**
   ```bash
   python scripts/api_client.py --url http://192.168.1.100:9000 health_check
   python scripts/api_client.py --host 192.168.1.100 --port 9000 get_tasks
   python scripts/api_client.py --env production health_check
   ```

2. **環境変数**
   ```bash
   export TODO_API_URL="http://192.168.1.100:9000"
   export TODO_API_HOST="192.168.1.100"
   export TODO_API_PORT="9000"
   export TODO_API_ENV="development"
   ```

3. **設定ファイル (config.json)**
   ```json
   {
     "environments": {
       "local": {"base_url": "http://localhost:8000"},
       "development": {"base_url": "http://localhost:9000"},
       "staging": {"base_url": "http://staging-server:8000"},
       "production": {"base_url": "http://production-server:8000"}
     }
   }
   ```

4. **デフォルト値**: `http://localhost:8000`

---

## 🧪 テスト

### スモークテスト実行

```bash
# 完全版（推奨）
python scripts/smoke_test.py

# 詳細出力
python scripts/smoke_test.py --verbose

# 高速版（Linux/macOS）
bash scripts/quick_test.sh

# 高速版（Windows）
.\scripts\quick_test.ps1
```

### CI/CD統合

```yaml
# GitHub Actions
name: Smoke Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start API
        run: docker-compose up -d
      - name: Smoke Test
        run: python .claude/skills/todo-api-knowledge/scripts/smoke_test.py
```

---

## 📖 ドキュメント

| ファイル | 説明 |
|---------|------|
| [`SKILL.md`](SKILL.md) | プロジェクト全知識（API仕様、アーキテクチャ、ベストプラクティス） |
| [`API_CLIENT_USAGE.md`](API_CLIENT_USAGE.md) | API Client詳細ガイド（接続設定、使用例） |
| [`SMOKE_TEST_GUIDE.md`](SMOKE_TEST_GUIDE.md) | スモークテストガイド（実行方法、CI/CD統合） |
| `config.json` | 環境別設定ファイル |
| `resources/api_examples.json` | API使用例・ワークフロー定義 |

---

## 🔧 メンテナンス

### SKILL.mdの更新

プロジェクトの仕様が変更された場合：

```bash
# 1. SKILL.mdを編集
vim SKILL.md

# 2. Claude Code再起動
# Skillの変更を反映
```

### api_client.pyの拡張

新しいAPIエンドポイントが追加された場合：

```python
# scripts/api_client.py に新メソッド追加
def new_api_method(self, param):
    """新しいAPI機能"""
    return self._request("POST", "/new-endpoint/", {"param": param})
```

### api_examples.jsonの更新

新しいワークフローや使用例を追加：

```json
{
  "examples": {
    "new_feature": {
      "description": "新機能の例",
      "method": "POST",
      "endpoint": "/new-endpoint/",
      "request_body": {...}
    }
  }
}
```

---

## 🐛 トラブルシューティング

### Skillが認識されない

```bash
# 1. ディレクトリ構造確認
ls -la .claude/skills/todo-api-knowledge/

# 2. SKILL.mdのYAMLフロントマター確認
head -5 SKILL.md

# 3. Claude Code再起動
```

### スクリプトが実行できない

```bash
# 1. 実行権限付与
chmod +x scripts/*.py scripts/*.sh

# 2. 依存関係確認
pip install requests

# 3. APIサーバー起動確認
curl http://localhost:8000/
```

### 接続エラー

```bash
# APIサーバーの起動確認
curl http://localhost:8000/

# ポート確認
netstat -an | grep 8000

# 使用中のURL確認
python scripts/api_client.py health_check 2>&1 | grep "Using API URL"
```

---

## 📊 コンテキストウィンドウ最適化

### 従来のMCP方式

```
ユーザー: 「タスク一覧を見せて」
→ MCP経由でAPI呼び出し
→ 全タスクデータ（100件×200トークン = 20,000トークン）をコンテキストに追加
→ コンテキストウィンドウを大量消費
```

### Claude Skills方式

```
ユーザー: 「タスク一覧取得のAPIは?」
→ Skillから該当部分のみ読み込み（約500トークン）
→ API仕様を説明
→ 必要に応じてスクリプト実行（結果のみ追加、約1,000トークン）
→ コンテキストウィンドウを最小限に使用
```

**削減率**: 約**90%**のコンテキスト削減を実現

---

## 🎉 まとめ

### このSkillを使用することで

- ✅ **遅延ロード**: 必要な情報のみを読み込み
- ✅ **効率的な知識共有**: 繰り返しプロジェクト情報を提供する必要なし
- ✅ **一貫性**: 常に最新のプロジェクト仕様を参照
- ✅ **スクリプト実行**: 必要に応じてAPIを直接呼び出し可能
- ✅ **柔軟な接続設定**: 複数の方法で接続先を指定可能
- ✅ **スモークテスト**: 3種類のテストで品質保証

### 提供される知識

- **API仕様**: 全エンドポイントの詳細
- **アーキテクチャ**: FastAPI + SQLAlchemy + Celery
- **ベストプラクティス**: TDD、レビュー、バックアップ
- **トラブルシューティング**: よくある問題と解決方法

---

## 📞 サポート

- **プロジェクトルート**: `D:\todo_api_fastapi`
- **Skillディレクトリ**: `D:\todo_api_fastapi\.claude\skills\todo-api-knowledge`

---

**バージョン**: 1.0.0
**最終更新**: 2025年10月19日

Claude Codeを再起動して、このSkillをお試しください！🚀
