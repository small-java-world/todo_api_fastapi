import logging
from typing import Any, Dict

from celery import current_task

from app.core.database import SessionLocal
from app.models.task import Task, TaskType
from app.services.task_service import TaskService
from app.celery_tasks.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_task_notification(
    self, task_id: int, notification_type: str, data: Dict[str, Any]
):
    """タスク通知の非同期処理"""
    try:
        db = SessionLocal()
        try:
            task_service = TaskService(db)
            task = task_service.get_task(task_id)

            if not task:
                logger.error(f"Task {task_id} not found for notification")
                return {"status": "error", "message": "Task not found"}

            # 通知タイプに応じた処理
            if notification_type == "status_change":
                logger.info(f"Processing status change notification for task {task_id}")
                # 実際の通知処理（メール、Slack等）をここに実装

            elif notification_type == "comment_added":
                logger.info(f"Processing comment notification for task {task_id}")
                # コメント追加の通知処理

            elif notification_type == "deadline_approaching":
                logger.info(f"Processing deadline notification for task {task_id}")
                # 期限接近の通知処理

            return {"status": "success", "message": "Notification processed"}

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Error processing notification for task {task_id}: {str(exc)}")
        # リトライ設定
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(bind=True)
def generate_task_report(self, task_ids: list, report_type: str):
    """タスクレポートの非同期生成"""
    try:
        db = SessionLocal()
        try:
            task_service = TaskService(db)

            # レポート生成処理
            if report_type == "hierarchical_summary":
                logger.info(
                    f"Generating hierarchical summary for {len(task_ids)} tasks"
                )
                # 階層構造サマリーの生成

            elif report_type == "status_distribution":
                logger.info(f"Generating status distribution for {len(task_ids)} tasks")
                # 状態分布レポートの生成

            elif report_type == "progress_tracking":
                logger.info(f"Generating progress tracking for {len(task_ids)} tasks")
                # 進捗追跡レポートの生成

            return {"status": "success", "message": f"{report_type} report generated"}

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Error generating {report_type} report: {str(exc)}")
        raise self.retry(exc=exc, countdown=120, max_retries=2)


@celery_app.task(bind=True)
def cleanup_old_data(self, days_old: int = 30):
    """古いデータのクリーンアップ"""
    try:
        db = SessionLocal()
        try:
            from datetime import datetime, timedelta

            from sqlalchemy import text

            cutoff_date = datetime.now() - timedelta(days=days_old)

            # 古い履歴データの削除
            deleted_history = db.execute(
                text("DELETE FROM task_history WHERE created_at < :cutoff_date"),
                {"cutoff_date": cutoff_date},
            ).rowcount

            # 古いコメントの削除（オプション）
            deleted_comments = db.execute(
                text("DELETE FROM comments WHERE created_at < :cutoff_date"),
                {"cutoff_date": cutoff_date},
            ).rowcount

            db.commit()

            logger.info(
                f"Cleanup completed: {deleted_history} history records, {deleted_comments} comments deleted"
            )
            return {
                "status": "success",
                "deleted_history": deleted_history,
                "deleted_comments": deleted_comments,
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Error during cleanup: {str(exc)}")
        raise self.retry(exc=exc, countdown=300, max_retries=1)


@celery_app.task(bind=True)
def validate_hierarchical_integrity(self):
    """階層構造の整合性チェック"""
    try:
        db = SessionLocal()
        try:
            task_service = TaskService(db)

            # 全タスクを取得
            all_tasks = task_service.get_tasks()

            integrity_issues = []

            for task in all_tasks:
                # 親子関係の整合性チェック
                if task.parent_id:
                    parent = task_service.get_task(task.parent_id)
                    if not parent:
                        integrity_issues.append(
                            f"Task {task.id} has invalid parent_id {task.parent_id}"
                        )
                    elif not task_service.hierarchical_id_service.validate_parent_child_relationship(
                        parent, task.type
                    ):
                        integrity_issues.append(
                            f"Task {task.id} has invalid parent-child relationship"
                        )

                # 階層IDの形式チェック
                if not task.hierarchical_id:
                    integrity_issues.append(f"Task {task.id} has no hierarchical_id")
                elif (
                    task.type == TaskType.requirement
                    and not task.hierarchical_id.startswith("REQ-")
                ):
                    integrity_issues.append(
                        f"Task {task.id} has invalid hierarchical_id format"
                    )
                elif task.type == TaskType.task and ".TSK-" not in task.hierarchical_id:
                    integrity_issues.append(
                        f"Task {task.id} has invalid hierarchical_id format"
                    )
                elif (
                    task.type == TaskType.subtask
                    and ".SUB-" not in task.hierarchical_id
                ):
                    integrity_issues.append(
                        f"Task {task.id} has invalid hierarchical_id format"
                    )

            if integrity_issues:
                logger.warning(
                    f"Hierarchical integrity issues found: {integrity_issues}"
                )
                return {"status": "warning", "issues": integrity_issues}
            else:
                logger.info("Hierarchical integrity check passed")
                return {"status": "success", "message": "No integrity issues found"}

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Error during integrity check: {str(exc)}")
        raise self.retry(exc=exc, countdown=60, max_retries=2)
