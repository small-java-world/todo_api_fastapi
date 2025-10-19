from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # データベース設定
    database_url: str = "sqlite:///./todo.db"

    # Redis設定（Celery用）
    redis_url: str = "redis://localhost:6379/0"

    # API設定
    api_title: str = "TODO API"
    api_version: str = "1.0.0"

    # CAS設定
    cas_root_path: str = "./blobs"

    # ファイル格納設定
    file_storage_root: str = "./storage"
    git_repo_path: str = "./git_repo"

    model_config = {"extra": "ignore"}

    def get_cas_root_path(self) -> Path:
        """CASルートパスを取得（絶対パスに変換）"""
        return Path(self.cas_root_path).resolve()

    def get_file_storage_root(self) -> Path:
        """ファイル格納ルートパスを取得（絶対パスに変換）"""
        return Path(self.file_storage_root).resolve()

    def get_git_repo_path(self) -> Path:
        """Gitリポジトリパスを取得（絶対パスに変換）"""
        return Path(self.git_repo_path).resolve()


settings = Settings()
