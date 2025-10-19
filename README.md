# TODO API with Hierarchical ID Structure

階層ID構造を採用したTODO管理APIです。三階層構造（要件 → タスク → サブタスク）でタスクを管理し、AIと人間の両方にとって分かりやすいID体系を提供します。

## 🚀 特徴

- **階層ID構造**: `REQ-001.TSK-002.SUB-003` 形式の分かりやすいID
- **三階層管理**: 要件 → タスク → サブタスクの階層構造
- **RESTful API**: 標準的なREST API設計
- **包括的テスト**: 100以上のテストケースで品質保証
- **Docker/Podman対応**: コンテナ化による簡単デプロイ
- **TDD開発**: テスト駆動開発による高品質実装
- **Git統合**: Gitリポジトリとの連携機能
- **レビュー機能**: コードレビュー管理システム
- **バックアップ機能**: 自動バックアップとリストア
- **CAS統合**: Content-Addressable Storageによる効率的なファイル管理

## 📋 階層ID構造

```
REQ-001 (ユーザー認証要件)
├── REQ-001.TSK-001 (ログインAPI実装)
│   ├── REQ-001.TSK-001.SUB-001 (パスワードハッシュ化)
│   └── REQ-001.TSK-001.SUB-002 (セッション管理)
└── REQ-001.TSK-002 (ユーザー登録API実装)
    └── REQ-001.TSK-002.SUB-001 (メール認証)
```

## 🛠️ 技術スタック

- **FastAPI**: モダンなPython Webフレームワーク
- **SQLAlchemy**: Python ORM
- **SQLite**: 軽量データベース
- **Pydantic**: データバリデーション
- **pytest**: テストフレームワーク
- **Docker**: コンテナ化
- **Alembic**: データベースマイグレーション
- **Celery**: 非同期タスク処理
- **Redis**: キャッシュ・メッセージブローカー
- **Git**: バージョン管理統合
- **mypy**: 静的型チェック
- **isort**: インポート順序管理

## 🚀 クイックスタート

### 1. 環境構築

#### Docker使用の場合
```bash
# リポジトリクローン
git clone <repository-url>
cd todo_api_fastapi

# Docker Composeで起動
docker-compose up -d
```

#### Podman使用の場合
```bash
# リポジトリクローン
git clone <repository-url>
cd todo_api_fastapi

# Podmanで起動 (Linux/macOS)
./start-podman.sh

# または PowerShell (Windows)
.\start-podman.ps1
```

**Podmanの利点:**
- **ルートレス**: 管理者権限不要でコンテナを実行
- **セキュリティ**: より安全なコンテナ実行環境
- **互換性**: Docker Composeファイルと互換
- **軽量**: より軽量なリソース使用

### 2. 動作確認
```bash
# ヘルスチェック
curl http://localhost:8000/
# => {"message":"TODO API Ready"}

# 要件作成
curl -X POST http://localhost:8000/tasks/requirements/ \
  -H "Content-Type: application/json" \
  -d '{"title": "ユーザー認証要件", "description": "認証機能の要件"}'

# タスク作成
curl -X POST http://localhost:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "ログインAPI", "type": "task", "parent_id": 1}'
```

### 3. テスト実行

#### Docker使用の場合
```bash
# 全テスト実行
docker-compose exec todo-api python -m pytest tests/ -v

# 統合テストのみ
docker-compose exec todo-api python -m pytest tests/test_integration.py -v
```

#### Podman使用の場合
```bash
# 全テスト実行 (Linux/macOS)
./test-podman.sh

# または PowerShell (Windows)
.\test-podman.ps1

# 個別テスト実行
podman-compose -f podman-compose.yml exec todo-api python -m pytest tests/test_integration.py -v
```

## 📚 API仕様

### エンドポイント一覧

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/tasks/` | タスク一覧取得 |
| POST | `/tasks/` | タスク作成 |
| POST | `/tasks/requirements/` | 要件作成 |
| GET | `/tasks/{id}` | タスク詳細取得 |
| PUT | `/tasks/{id}` | タスク更新 |
| DELETE | `/tasks/{id}` | タスク削除 |
| GET | `/tasks/tree/` | タスクツリー表示 |
| GET | `/reviews/` | レビュー一覧取得 |
| POST | `/reviews/` | レビュー作成 |
| GET | `/artifacts/` | アーティファクト一覧 |
| POST | `/artifacts/` | アーティファクト作成 |
| GET | `/backup/` | バックアップ一覧 |
| POST | `/backup/` | バックアップ作成 |

### レスポンス例

#### 要件作成
```json
{
  "id": 1,
  "hierarchical_id": "REQ-001",
  "title": "ユーザー認証要件",
  "description": "認証機能の要件",
  "type": "requirement",
  "status": "not_started",
  "parent_id": null,
  "created_at": "2025-10-19T04:56:36",
  "updated_at": null
}
```

#### タスク作成
```json
{
  "id": 2,
  "hierarchical_id": "REQ-001.TSK-001",
  "title": "ログインAPI",
  "description": "ログイン機能のAPI実装",
  "type": "task",
  "status": "not_started",
  "parent_id": 1,
  "created_at": "2025-10-19T04:56:36",
  "updated_at": null
}
```

## 🧪 テスト構成

### テストカテゴリ
- **単体テスト**: 55テスト（基本CRUD操作・サービス層）
- **統合テスト**: 17テスト（階層構造ワークフロー）
- **データベーステスト**: 8テスト（制約・一貫性）
- **レビューテスト**: 22テスト（レビュー機能）
- **バックアップテスト**: 16テスト（バックアップ機能）
- **Git統合テスト**: 26テスト（Git連携）
- **CAS統合テスト**: 15テスト（ファイル管理）
- **パフォーマンステスト**: 8テスト（大量データ処理）

### テスト実行
```bash
# 全テスト
docker-compose exec todo-api python -m pytest tests/ -v

# カテゴリ別テスト
docker-compose exec todo-api python -m pytest tests/test_integration.py -v
docker-compose exec todo-api python -m pytest tests/test_database_integration.py -v
docker-compose exec todo-api python -m pytest tests/test_review_service_ut.py -v
docker-compose exec todo-api python -m pytest tests/test_backup_service_ut.py -v
docker-compose exec todo-api python -m pytest tests/test_git_service_ut.py -v
docker-compose exec todo-api python -m pytest tests/test_performance.py -v

# 型チェック
docker-compose exec todo-api python -m mypy app/ --ignore-missing-imports --explicit-package-bases

# インポート順序チェック
docker-compose exec todo-api python -m isort --check-only app/ --settings-path pyproject.toml
```

## 📊 パフォーマンス仕様

- **要件作成**: 100件/30秒以内
- **タスク作成**: 50件/20秒以内
- **サブタスク作成**: 30件/15秒以内
- **クエリ応答**: 1秒以内（大量データ時）

## 🔧 開発環境

### 必要な環境

#### Docker使用の場合
- Docker & Docker Compose
- Python 3.10+ (ローカル開発時)
- Git

#### Podman使用の場合
- Podman & podman-compose
- Python 3.10+ (ローカル開発時)
- Git
- (Windows) PowerShell または WSL2

### 開発ワークフロー
```bash
# 1. フィーチャーブランチ作成
git checkout -b feature/new-feature

# 2. テスト駆動開発
# - テスト作成 → 実装 → リファクタリング

# 3. テスト実行
docker-compose exec todo-api python -m pytest tests/ -v

# 4. コミット
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

## 📁 プロジェクト構造

```
todo_api_fastapi/
├── app/                           # アプリケーションコード
│   ├── api/                      # APIエンドポイント
│   │   ├── tasks.py              # タスクAPI
│   │   ├── tree.py               # ツリー表示API
│   │   ├── reviews.py            # レビューAPI
│   │   ├── artifacts.py          # アーティファクトAPI
│   │   ├── backup.py             # バックアップAPI
│   │   └── storage.py            # ストレージAPI
│   ├── celery_tasks/             # Celeryタスク
│   │   ├── tasks.py              # 非同期タスク
│   │   ├── backup_tasks.py       # バックアップタスク
│   │   └── worker.py             # Celeryワーカー
│   ├── core/                     # 設定・データベース
│   │   ├── config.py             # 設定管理
│   │   └── database.py           # データベース接続
│   ├── models/                   # データベースモデル
│   │   ├── task.py               # タスクモデル
│   │   ├── review.py             # レビューモデル
│   │   ├── artifact_model.py     # アーティファクトモデル
│   │   └── comment.py             # コメントモデル
│   ├── schemas/                  # Pydanticスキーマ
│   │   ├── task_schema.py        # タスクスキーマ
│   │   ├── review_schema.py      # レビュースキーマ
│   │   ├── backup_schema.py      # バックアップスキーマ
│   │   └── artifact.py           # アーティファクトスキーマ
│   └── services/                 # ビジネスロジック
│       ├── task_service.py       # タスクサービス
│       ├── review_service.py     # レビューサービス
│       ├── backup_service.py     # バックアップサービス
│       ├── git_service.py        # Gitサービス
│       ├── cas_service.py        # CASサービス
│       └── hierarchical_id_service.py # 階層IDサービス
├── tests/                        # テストコード
│   ├── test_git_service_ut.py    # Gitサービス単体テスト
│   ├── test_config_ut.py         # 設定単体テスト
│   ├── test_hierarchical_id_service_ut.py # 階層ID単体テスト
│   ├── test_review_service_ut.py # レビューサービス単体テスト
│   ├── test_backup_service_ut.py # バックアップサービス単体テスト
│   ├── test_integration.py       # 統合テスト
│   ├── test_database_integration.py # データベース統合テスト
│   └── test_performance.py       # パフォーマンステスト
├── docker-compose.yml            # Docker Compose設定
├── podman-compose.yml            # Podman Compose設定
├── Dockerfile                    # Docker設定
├── start-podman.sh              # Podman起動スクリプト (Linux/macOS)
├── stop-podman.sh               # Podman停止スクリプト (Linux/macOS)
├── test-podman.sh               # Podmanテストスクリプト (Linux/macOS)
├── start-podman.ps1             # Podman起動スクリプト (Windows)
├── stop-podman.ps1              # Podman停止スクリプト (Windows)
├── test-podman.ps1              # Podmanテストスクリプト (Windows)
├── requirements.txt              # Python依存関係
├── pyproject.toml               # プロジェクト設定
└── README.md                    # このファイル
```

## 🔒 セキュリティ

- **入力検証**: Pydanticによる厳密なバリデーション
- **SQLインジェクション**: SQLAlchemy ORMによる防止
- **データ整合性**: 外部キー制約による保証
- **エラーハンドリング**: 適切なHTTPステータスコード

## 📈 監視・ログ

### ログレベル
- **INFO**: 一般的な操作ログ
- **WARNING**: 警告ログ
- **ERROR**: エラーログ
- **DEBUG**: デバッグログ

### メトリクス
- リクエスト数
- レスポンス時間
- エラー率
- データベース接続数

## 🚀 デプロイメント

### 本番環境
```bash
# 環境変数設定
export DATABASE_URL="postgresql://user:pass@localhost/todo"
export REDIS_URL="redis://localhost:6379/0"

# マイグレーション実行
alembic upgrade head

# アプリケーション起動
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker Compose
```yaml
version: '3.8'
services:
  todo-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./todo.db
    volumes:
      - .:/app
```

## 🤝 コントリビューション

1. フィーチャーブランチを作成
2. テストを書く
3. 実装する
4. テストを実行
5. プルリクエストを作成

### コーディング規約
- PEP 8準拠
- 型ヒント必須
- ドキュメント文字列必須
- テストカバレッジ90%以上

## 📞 サポート

### トラブルシューティング
```bash
# ログ確認
docker-compose logs todo-api

# データベース確認
docker-compose exec todo-api python -c "from app.core.database import engine; print(engine)"

# テスト実行
docker-compose exec todo-api python -m pytest tests/ -v
```

### よくある問題
1. **ポート競合**: 8000番ポートが使用中
2. **データベースエラー**: SQLiteファイルの権限問題
3. **テスト失敗**: データベースの状態不整合

## 📄 ライセンス

MIT License

## 📞 連絡先

- **開発者**: AI Assistant
- **バージョン**: 1.0.0
- **最終更新**: 2025年10月19日

---

**🎉 階層ID構造のTODO APIで、効率的なタスク管理を始めましょう！**
