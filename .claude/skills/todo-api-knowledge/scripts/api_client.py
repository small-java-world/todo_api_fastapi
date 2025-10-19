#!/usr/bin/env python3
"""
TODO API Client Script for Claude Skills

このスクリプトは、Claude CodeからTODO APIを呼び出すためのヘルパー関数を提供します。
Claude Skillsから実行可能で、コンテキストウィンドウを消費せずにAPIデータを取得できます。

環境変数による設定:
    TODO_API_URL: APIのベースURL（デフォルト: http://localhost:8000）
    TODO_API_HOST: APIホスト（デフォルト: localhost）
    TODO_API_PORT: APIポート（デフォルト: 8000）

使用例:
    # 環境変数で指定
    export TODO_API_URL="http://192.168.1.100:9000"
    python api_client.py get_tasks

    # コマンドライン引数で指定
    python api_client.py --url http://192.168.1.100:9000 get_tasks
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import requests


class TodoAPIClient:
    """TODO API クライアント"""

    def __init__(self, base_url: Optional[str] = None):
        """
        初期化

        Args:
            base_url: APIのベースURL
                      未指定時は以下の優先順位で決定:
                      1. 環境変数 TODO_API_URL
                      2. 環境変数 TODO_API_HOST と TODO_API_PORT から構築
                      3. デフォルト値 http://localhost:8000
        """
        if base_url is None:
            base_url = self._get_base_url_from_env()

        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _get_base_url_from_env(self) -> str:
        """
        環境変数・設定ファイルからベースURLを取得

        優先順位:
        1. 環境変数 TODO_API_URL
        2. 環境変数 TODO_API_HOST + TODO_API_PORT
        3. 環境変数 TODO_API_ENV で指定された環境の設定
        4. 設定ファイル (config.json)
        5. デフォルト値 (http://localhost:8000)

        Returns:
            ベースURL
        """
        # 1. TODO_API_URL が設定されている場合はそれを使用
        if "TODO_API_URL" in os.environ:
            return os.environ["TODO_API_URL"]

        # 2. TODO_API_HOST と TODO_API_PORT から構築
        if "TODO_API_HOST" in os.environ:
            host = os.environ["TODO_API_HOST"]
            port = os.environ.get("TODO_API_PORT", "8000")
            return f"http://{host}:{port}"

        # 3. TODO_API_ENV で指定された環境の設定を読み込み
        env_name = os.environ.get("TODO_API_ENV", "local")
        config = self._load_config()
        if config and "environments" in config and env_name in config["environments"]:
            return config["environments"][env_name]["base_url"]

        # 4. 設定ファイルのデフォルト値
        if config and "api" in config and "base_url" in config["api"]:
            return config["api"]["base_url"]

        # 5. デフォルト値
        return "http://localhost:8000"

    def _load_config(self) -> Optional[Dict[str, Any]]:
        """
        設定ファイルを読み込み

        Returns:
            設定データ、読み込み失敗時はNone
        """
        # スクリプトと同じディレクトリの親ディレクトリにある config.json を探す
        script_dir = Path(__file__).parent.parent
        config_path = script_dir / "config.json"

        if not config_path.exists():
            return None

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        APIリクエスト実行

        Args:
            method: HTTPメソッド (GET, POST, PUT, DELETE)
            endpoint: APIエンドポイント
            data: リクエストボディ

        Returns:
            レスポンスJSON

        Raises:
            requests.exceptions.RequestException: リクエスト失敗時
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "PUT":
                response = self.session.put(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error: API request failed - {e}", file=sys.stderr)
            raise

    # === タスク管理API ===

    def create_requirement(self, title: str, description: str = "") -> Dict[str, Any]:
        """
        要件作成

        Args:
            title: 要件タイトル
            description: 要件説明

        Returns:
            作成された要件データ
        """
        data = {"title": title, "description": description}
        return self._request("POST", "/tasks/requirements/", data)

    def create_task(
        self, title: str, parent_id: int, description: str = ""
    ) -> Dict[str, Any]:
        """
        タスク作成

        Args:
            title: タスクタイトル
            parent_id: 親要件ID
            description: タスク説明

        Returns:
            作成されたタスクデータ
        """
        data = {
            "title": title,
            "description": description,
            "type": "task",
            "parent_id": parent_id,
        }
        return self._request("POST", "/tasks/", data)

    def create_subtask(
        self, title: str, parent_id: int, description: str = ""
    ) -> Dict[str, Any]:
        """
        サブタスク作成

        Args:
            title: サブタスクタイトル
            parent_id: 親タスクID
            description: サブタスク説明

        Returns:
            作成されたサブタスクデータ
        """
        data = {
            "title": title,
            "description": description,
            "type": "subtask",
            "parent_id": parent_id,
        }
        return self._request("POST", "/tasks/", data)

    def get_tasks(self, skip: int = 0, limit: int = 100) -> list[Dict[str, Any]]:
        """
        タスク一覧取得

        Args:
            skip: スキップ数
            limit: 取得数

        Returns:
            タスクリスト
        """
        return self._request("GET", f"/tasks/?skip={skip}&limit={limit}")

    def get_task(self, task_id: int) -> Dict[str, Any]:
        """
        タスク詳細取得

        Args:
            task_id: タスクID

        Returns:
            タスクデータ
        """
        return self._request("GET", f"/tasks/{task_id}")

    def update_task(
        self, task_id: int, title: Optional[str] = None, status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        タスク更新

        Args:
            task_id: タスクID
            title: 新しいタイトル
            status: 新しいステータス

        Returns:
            更新されたタスクデータ
        """
        data = {}
        if title:
            data["title"] = title
        if status:
            data["status"] = status
        return self._request("PUT", f"/tasks/{task_id}", data)

    def delete_task(self, task_id: int) -> Dict[str, Any]:
        """
        タスク削除

        Args:
            task_id: タスクID

        Returns:
            削除結果
        """
        return self._request("DELETE", f"/tasks/{task_id}")

    def get_task_tree(self) -> Dict[str, Any]:
        """
        タスクツリー取得

        Returns:
            タスクツリーデータ
        """
        return self._request("GET", "/tasks/tree/")

    # === レビュー管理API ===

    def create_review(
        self,
        target_type: str,
        target_id: int,
        review_type: str,
        title: str,
        description: str = "",
        reviewer: str = "claude-code",
    ) -> Dict[str, Any]:
        """
        レビュー作成

        Args:
            target_type: レビュー対象タイプ (requirement, task, subtask)
            target_id: レビュー対象ID
            review_type: レビュータイプ
            title: レビュータイトル
            description: レビュー説明
            reviewer: レビュアー名

        Returns:
            作成されたレビューデータ
        """
        data = {
            "target_type": target_type,
            "target_id": target_id,
            "review_type": review_type,
            "title": title,
            "description": description,
            "reviewer": reviewer,
        }
        return self._request("POST", "/reviews/", data)

    def get_review_statistics(self) -> Dict[str, Any]:
        """
        レビュー統計取得

        Returns:
            レビュー統計データ
        """
        return self._request("GET", "/reviews/statistics")

    # === バックアップ管理API ===

    def create_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """
        バックアップ作成

        Args:
            backup_name: バックアップ名（省略時は自動生成）

        Returns:
            作成されたバックアップデータ
        """
        data = {}
        if backup_name:
            data["backup_name"] = backup_name
        return self._request("POST", "/backup/", data)

    def get_backups(self) -> list[Dict[str, Any]]:
        """
        バックアップ一覧取得

        Returns:
            バックアップリスト
        """
        return self._request("GET", "/backup/")

    def restore_backup(self, backup_id: int) -> Dict[str, Any]:
        """
        バックアップ復元

        Args:
            backup_id: バックアップID

        Returns:
            復元結果
        """
        return self._request("POST", f"/backup/{backup_id}/restore")

    def get_backup_statistics(self) -> Dict[str, Any]:
        """
        バックアップ統計取得

        Returns:
            バックアップ統計データ
        """
        return self._request("GET", "/backup/statistics")

    # === ヘルスチェック ===

    def health_check(self) -> Dict[str, Any]:
        """
        APIヘルスチェック

        Returns:
            ヘルスチェック結果
        """
        return self._request("GET", "/")


def main():
    """
    コマンドライン実行用メイン関数

    使用例:
        # デフォルトURL（localhost:8000）
        python api_client.py get_tasks

        # --url オプションでURL指定
        python api_client.py --url http://192.168.1.100:9000 get_tasks

        # --host と --port で個別指定
        python api_client.py --host 192.168.1.100 --port 9000 get_tasks

        # 環境変数で指定
        export TODO_API_URL="http://192.168.1.100:9000"
        python api_client.py get_tasks
    """
    # コマンドライン引数からURL情報を抽出
    base_url = None
    host = None
    port = None
    env_name = None
    args = sys.argv[1:]

    # --url, --host, --port, --env オプションを処理
    i = 0
    while i < len(args):
        if args[i] == "--url" and i + 1 < len(args):
            base_url = args[i + 1]
            args.pop(i)  # --url を削除
            args.pop(i)  # URL値を削除
        elif args[i] == "--host" and i + 1 < len(args):
            host = args[i + 1]
            args.pop(i)
            args.pop(i)
        elif args[i] == "--port" and i + 1 < len(args):
            port = args[i + 1]
            args.pop(i)
            args.pop(i)
        elif args[i] == "--env" and i + 1 < len(args):
            env_name = args[i + 1]
            args.pop(i)
            args.pop(i)
        else:
            i += 1

    # --env が指定された場合、環境変数を設定
    if env_name:
        os.environ["TODO_API_ENV"] = env_name

    # --host と --port からURLを構築
    if host and port:
        base_url = f"http://{host}:{port}"
    elif host:
        base_url = f"http://{host}:8000"

    if len(args) < 1:
        print("Usage: python api_client.py [options] <command> [args...]", file=sys.stderr)
        print("\nOptions:", file=sys.stderr)
        print("  --url <url>        APIのベースURL (例: http://localhost:8000)", file=sys.stderr)
        print("  --host <host>      APIホスト (例: localhost)", file=sys.stderr)
        print("  --port <port>      APIポート (例: 8000)", file=sys.stderr)
        print("  --env <env>        環境名 (例: local, development, staging, production)", file=sys.stderr)
        print("\nEnvironment Variables:", file=sys.stderr)
        print("  TODO_API_URL       APIのベースURL", file=sys.stderr)
        print("  TODO_API_HOST      APIホスト", file=sys.stderr)
        print("  TODO_API_PORT      APIポート", file=sys.stderr)
        print("  TODO_API_ENV       環境名（デフォルト: local）", file=sys.stderr)
        print("\nConfiguration File:", file=sys.stderr)
        print("  config.json で環境別の設定を管理可能", file=sys.stderr)
        print("\nAvailable commands:", file=sys.stderr)
        print("  health_check", file=sys.stderr)
        print("  get_tasks", file=sys.stderr)
        print("  get_task <task_id>", file=sys.stderr)
        print("  create_requirement <title> [description]", file=sys.stderr)
        print("  create_task <title> <parent_id> [description]", file=sys.stderr)
        print("  get_task_tree", file=sys.stderr)
        print("  get_review_statistics", file=sys.stderr)
        print("  get_backups", file=sys.stderr)
        print("  create_backup [backup_name]", file=sys.stderr)
        sys.exit(1)

    client = TodoAPIClient(base_url=base_url)
    command = args[0]

    # デバッグ情報出力
    print(f"# Using API URL: {client.base_url}", file=sys.stderr)

    try:
        if command == "health_check":
            result = client.health_check()

        elif command == "get_tasks":
            result = client.get_tasks()

        elif command == "get_task":
            if len(args) < 2:
                print("Error: task_id required", file=sys.stderr)
                sys.exit(1)
            task_id = int(args[1])
            result = client.get_task(task_id)

        elif command == "create_requirement":
            if len(args) < 2:
                print("Error: title required", file=sys.stderr)
                sys.exit(1)
            title = args[1]
            description = args[2] if len(args) > 2 else ""
            result = client.create_requirement(title, description)

        elif command == "create_task":
            if len(args) < 3:
                print("Error: title and parent_id required", file=sys.stderr)
                sys.exit(1)
            title = args[1]
            parent_id = int(args[2])
            description = args[3] if len(args) > 3 else ""
            result = client.create_task(title, parent_id, description)

        elif command == "get_task_tree":
            result = client.get_task_tree()

        elif command == "get_review_statistics":
            result = client.get_review_statistics()

        elif command == "get_backups":
            result = client.get_backups()

        elif command == "create_backup":
            backup_name = args[1] if len(args) > 1 else None
            result = client.create_backup(backup_name)

        else:
            print(f"Error: Unknown command '{command}'", file=sys.stderr)
            sys.exit(1)

        # 結果をJSON形式で出力
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
