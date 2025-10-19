import logging
from pathlib import Path

from app.core.database import SessionLocal
from app.services.backup_service import BackupService
from app.tasks.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def create_scheduled_backup(backup_name: str = None):
    """スケジュールされたバックアップを作成"""
    with SessionLocal() as db:
        backup_service = BackupService(db)
        try:
            result = backup_service.create_backup(backup_name)
            logger.info(f"Scheduled backup completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Scheduled backup failed: {str(e)}")
            raise


@celery_app.task
def cleanup_old_backups_task(days_to_keep: int = 30):
    """古いバックアップをクリーンアップ"""
    with SessionLocal() as db:
        backup_service = BackupService(db)
        try:
            result = backup_service.cleanup_old_backups(days_to_keep)
            logger.info(f"Backup cleanup completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Backup cleanup failed: {str(e)}")
            raise


@celery_app.task
def backup_health_check():
    """バックアップシステムのヘルスチェック"""
    with SessionLocal() as db:
        backup_service = BackupService(db)
        try:
            # 最新のバックアップを確認
            backups = backup_service.list_backups()

            if not backups:
                logger.warning("No backups found")
                return {"status": "warning", "message": "No backups found"}

            # 最新バックアップの情報を取得
            latest_backup = backups[0]
            backup_info = backup_service.get_backup_info(latest_backup["backup_name"])

            if backup_info.get("status") == "failed":
                logger.error(
                    f"Latest backup is corrupted: {latest_backup['backup_name']}"
                )
                return {"status": "error", "message": "Latest backup is corrupted"}

            logger.info(f"Backup health check passed: {len(backups)} backups found")
            return {
                "status": "healthy",
                "total_backups": len(backups),
                "latest_backup": latest_backup["backup_name"],
                "latest_backup_size": backup_info.get("size", 0),
            }
        except Exception as e:
            logger.error(f"Backup health check failed: {str(e)}")
            return {"status": "error", "message": str(e)}


@celery_app.task
def backup_verification(backup_name: str):
    """バックアップの整合性を検証"""
    with SessionLocal() as db:
        backup_service = BackupService(db)
        try:
            backup_info = backup_service.get_backup_info(backup_name)

            if backup_info.get("status") == "failed":
                return {"status": "failed", "message": "Backup not found or corrupted"}

            # バックアップファイルの存在確認
            backup_path = backup_info["backup_path"]
            required_files = ["metadata.json"]

            # データベースファイルまたはSQLダンプの存在確認
            db_file = Path(backup_path) / "database.db"
            sql_dump = Path(backup_path) / "database_dump.sql"

            if not db_file.exists() and not sql_dump.exists():
                return {
                    "status": "failed",
                    "message": "No database file found in backup",
                }

            # メタデータファイルの検証
            metadata_file = Path(backup_path) / "metadata.json"
            if not metadata_file.exists():
                return {"status": "failed", "message": "Metadata file not found"}

            logger.info(f"Backup verification passed: {backup_name}")
            return {
                "status": "verified",
                "backup_name": backup_name,
                "backup_size": backup_info.get("size", 0),
                "files_count": len(backup_info.get("files", [])),
            }
        except Exception as e:
            logger.error(f"Backup verification failed: {str(e)}")
            return {"status": "error", "message": str(e)}
