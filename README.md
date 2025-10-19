# TODO API with Hierarchical ID Structure

階層ID構造を採用したTODO管理APIです。三階層構造（要件 → タスク → サブタスク）でタスクを管理し、AIと人間の両方にとって分かりやすいID体系を提供します。

## 🚀 特徴

- **階層ID構造**: `REQ-001.TSK-002.SUB-003` 形式の分かりやすいID
- **三階層管理**: 要件 → タスク → サブタスクの階層構造
- **RESTful API**: 標準的なREST API設計
- **包括的テスト**: 50以上のテストケースで品質保証
- **Docker対応**: コンテナ化による簡単デプロイ
- **TDD開発**: テスト駆動開発による高品質実装

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

## 🚀 クイックスタート

### 1. 環境構築
```bash
# リポジトリクローン
git clone <repository-url>
cd todo_api_fastapi

# Docker Composeで起動
docker-compose up -d
```

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
```bash
# 全テスト実行
docker-compose exec todo-api python -m pytest tests/ -v

# 統合テストのみ
docker-compose exec todo-api python -m pytest tests/test_integration.py -v
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
- **単体テスト**: 8テスト（基本CRUD操作）
- **統合テスト**: 9テスト（階層構造ワークフロー）
- **データベーステスト**: 8テスト（制約・一貫性）
- **エラーテスト**: 17テスト（バリデーション）
- **パフォーマンステスト**: 8テスト（大量データ処理）

### テスト実行
```bash
# 全テスト
docker-compose exec todo-api python -m pytest tests/ -v

# カテゴリ別テスト
docker-compose exec todo-api python -m pytest tests/test_integration.py -v
docker-compose exec todo-api python -m pytest tests/test_performance.py -v
docker-compose exec todo-api python -m pytest tests/test_error_cases.py -v
```

## 📊 パフォーマンス仕様

- **要件作成**: 100件/30秒以内
- **タスク作成**: 50件/20秒以内
- **サブタスク作成**: 30件/15秒以内
- **クエリ応答**: 1秒以内（大量データ時）

## 🔧 開発環境

### 必要な環境
- Docker & Docker Compose
- Python 3.10+ (ローカル開発時)
- Git

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
├── app/                    # アプリケーションコード
│   ├── api/               # APIエンドポイント
│   ├── core/              # 設定・データベース
│   ├── models/            # データベースモデル
│   ├── schemas/           # Pydanticスキーマ
│   ├── services/          # ビジネスロジック
│   └── tasks/             # Celeryタスク
├── tests/                 # テストコード
│   ├── test_tasks.py      # 単体テスト
│   ├── test_integration.py # 統合テスト
│   ├── test_database_integration.py # データベーステスト
│   ├── test_error_cases.py # エラーテスト
│   └── test_performance.py # パフォーマンステスト
├── migrations/            # Alembicマイグレーション
├── docker-compose.yml     # Docker Compose設定
├── Dockerfile            # Docker設定
├── requirements.txt      # Python依存関係
├── API仕様書.md          # API仕様書
├── 技術仕様書.md         # 技術仕様書
└── README.md             # このファイル
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
