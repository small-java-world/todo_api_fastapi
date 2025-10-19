import json
import logging
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine

logger = logging.getLogger(__name__)


class BackupService:
    """データベースバックアップサービス"""

    def __init__(self, db: Session):
        self.db = db
        self.backup_root = settings.get_file_storage_root() / "backups"
        self.backup_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"Backup root: {self.backup_root}")

    def create_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """データベースバックアップを作成"""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"

        backup_dir = self.backup_root / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            # SQLiteデータベースファイルをコピー
            db_path = self._get_database_path()
            if db_path and db_path.exists():
                backup_db_path = backup_dir / "database.db"
                shutil.copy2(db_path, backup_db_path)
                logger.info(f"Database backed up to: {backup_db_path}")
            else:
                # SQLite以外のデータベースの場合、SQLダンプを作成
                self._create_sql_dump(backup_dir)

            # メタデータを作成
            metadata = {
                "backup_name": backup_name,
                "created_at": datetime.now().isoformat(),
                "database_url": settings.database_url,
                "backup_type": "full",
                "version": "1.0.0",
            }

            metadata_path = backup_dir / "metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"Backup created successfully: {backup_name}")
            return {
                "backup_name": backup_name,
                "backup_path": str(backup_dir),
                "created_at": metadata["created_at"],
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return {"backup_name": backup_name, "status": "failed", "error": str(e)}

    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """バックアップからデータベースを復元"""
        backup_dir = self.backup_root / backup_name

        if not backup_dir.exists():
            return {"status": "failed", "error": f"Backup not found: {backup_name}"}

        try:
            # メタデータを読み込み
            metadata_path = backup_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            else:
                metadata = {}

            # 現在のデータベースをバックアップ
            current_backup_name = (
                f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self.create_backup(current_backup_name)

            # データベースを復元
            db_path = self._get_database_path()
            if db_path and db_path.exists():
                backup_db_path = backup_dir / "database.db"
                if backup_db_path.exists():
                    shutil.copy2(backup_db_path, db_path)
                    logger.info(f"Database restored from: {backup_db_path}")
                else:
                    # SQLダンプから復元
                    self._restore_from_sql_dump(backup_dir)

            logger.info(f"Backup restored successfully: {backup_name}")
            return {
                "backup_name": backup_name,
                "status": "success",
                "restored_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Backup restore failed: {str(e)}")
            return {"backup_name": backup_name, "status": "failed", "error": str(e)}

    def list_backups(self) -> List[Dict[str, Any]]:
        """バックアップ一覧を取得"""
        backups = []

        for backup_dir in self.backup_root.iterdir():
            if backup_dir.is_dir():
                metadata_path = backup_dir / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                        backups.append(
                            {
                                "backup_name": backup_dir.name,
                                "created_at": metadata.get("created_at"),
                                "backup_type": metadata.get("backup_type", "full"),
                                "size": self._get_backup_size(backup_dir),
                            }
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to read metadata for {backup_dir.name}: {str(e)}"
                        )
                        backups.append(
                            {
                                "backup_name": backup_dir.name,
                                "created_at": None,
                                "backup_type": "unknown",
                                "size": self._get_backup_size(backup_dir),
                            }
                        )

        # 作成日時でソート（新しい順）
        backups.sort(key=lambda x: x["created_at"] or "", reverse=True)
        return backups

    def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """バックアップを削除"""
        backup_dir = self.backup_root / backup_name

        if not backup_dir.exists():
            return {"status": "failed", "error": f"Backup not found: {backup_name}"}

        try:
            shutil.rmtree(backup_dir)
            logger.info(f"Backup deleted: {backup_name}")
            return {
                "backup_name": backup_name,
                "status": "success",
                "deleted_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Backup deletion failed: {str(e)}")
            return {"backup_name": backup_name, "status": "failed", "error": str(e)}

    def cleanup_old_backups(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """古いバックアップをクリーンアップ"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        errors = []

        for backup_dir in self.backup_root.iterdir():
            if backup_dir.is_dir():
                metadata_path = backup_dir / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)

                        created_at_str = metadata.get("created_at")
                        if created_at_str:
                            created_at = datetime.fromisoformat(created_at_str)
                            if created_at < cutoff_date:
                                shutil.rmtree(backup_dir)
                                deleted_count += 1
                                logger.info(f"Old backup deleted: {backup_dir.name}")
                    except Exception as e:
                        error_msg = f"Failed to process {backup_dir.name}: {str(e)}"
                        errors.append(error_msg)
                        logger.warning(error_msg)

        return {
            "deleted_count": deleted_count,
            "errors": errors,
            "status": "success" if not errors else "partial",
        }

    def get_backup_info(self, backup_name: str) -> Dict[str, Any]:
        """バックアップの詳細情報を取得"""
        backup_dir = self.backup_root / backup_name

        if not backup_dir.exists():
            return {"status": "failed", "error": f"Backup not found: {backup_name}"}

        try:
            metadata_path = backup_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            else:
                metadata = {}

            return {
                "backup_name": backup_name,
                "backup_path": str(backup_dir),
                "size": self._get_backup_size(backup_dir),
                "created_at": metadata.get("created_at"),
                "backup_type": metadata.get("backup_type", "full"),
                "database_url": metadata.get("database_url"),
                "version": metadata.get("version", "1.0.0"),
                "files": self._list_backup_files(backup_dir),
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _get_database_path(self) -> Optional[Path]:
        """データベースファイルのパスを取得"""
        db_url = settings.database_url

        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            return Path(db_path)
        elif db_url.startswith("sqlite://"):
            db_path = db_url.replace("sqlite://", "")
            return Path(db_path)

        return None

    def _create_sql_dump(self, backup_dir: Path):
        """SQLダンプを作成"""
        dump_path = backup_dir / "database_dump.sql"

        # PostgreSQLの場合
        if settings.database_url.startswith("postgresql://"):
            subprocess.run(
                ["pg_dump", settings.database_url],
                stdout=open(dump_path, "w"),
                check=True,
            )
        # MySQLの場合
        elif settings.database_url.startswith("mysql://"):
            subprocess.run(
                ["mysqldump", settings.database_url],
                stdout=open(dump_path, "w"),
                check=True,
            )
        else:
            # SQLAlchemyを使用してダンプを作成
            self._create_sqlalchemy_dump(dump_path)

    def _restore_from_sql_dump(self, backup_dir: Path):
        """SQLダンプから復元"""
        dump_path = backup_dir / "database_dump.sql"

        if not dump_path.exists():
            raise FileNotFoundError("SQL dump file not found")

        # PostgreSQLの場合
        if settings.database_url.startswith("postgresql://"):
            subprocess.run(
                ["psql", settings.database_url], stdin=open(dump_path, "r"), check=True
            )
        # MySQLの場合
        elif settings.database_url.startswith("mysql://"):
            subprocess.run(
                ["mysql", settings.database_url], stdin=open(dump_path, "r"), check=True
            )
        else:
            # SQLAlchemyを使用して復元
            self._restore_from_sqlalchemy_dump(dump_path)

    def _create_sqlalchemy_dump(self, dump_path: Path):
        """SQLAlchemyを使用してダンプを作成"""
        from sqlalchemy import text

        with open(dump_path, "w", encoding="utf-8") as f:
            # テーブル構造をダンプ
            result = self.db.execute(
                text("SELECT sql FROM sqlite_master WHERE type='table'")
            )
            for row in result:
                f.write(f"{row[0]};\n")

            # データをダンプ
            result = self.db.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            for row in result:
                table_name = row[0]
                if table_name != "sqlite_sequence":
                    result = self.db.execute(text(f"SELECT * FROM {table_name}"))
                    for data_row in result:
                        values = ", ".join(
                            f"'{str(v)}'" if v is not None else "NULL" for v in data_row
                        )
                        f.write(f"INSERT INTO {table_name} VALUES ({values});\n")

    def _restore_from_sqlalchemy_dump(self, dump_path: Path):
        """SQLAlchemyを使用してダンプから復元"""
        from sqlalchemy import text

        with open(dump_path, "r", encoding="utf-8") as f:
            sql_statements = f.read().split(";")
            for statement in sql_statements:
                statement = statement.strip()
                if statement:
                    try:
                        self.db.execute(text(statement))
                    except Exception as e:
                        logger.warning(
                            f"Failed to execute SQL: {statement[:100]}... Error: {str(e)}"
                        )

        self.db.commit()

    def _get_backup_size(self, backup_dir: Path) -> int:
        """バックアップのサイズを取得"""
        total_size = 0
        for file_path in backup_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size

    def _list_backup_files(self, backup_dir: Path) -> List[Dict[str, Any]]:
        """バックアップ内のファイル一覧を取得"""
        files = []
        for file_path in backup_dir.rglob("*"):
            if file_path.is_file():
                files.append(
                    {
                        "name": file_path.name,
                        "path": str(file_path.relative_to(backup_dir)),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                    }
                )
        return files
