from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, asc, desc, or_
from sqlalchemy.orm import Session

from app.models.comment import Comment as CommentModel
from app.models.task import Task, TaskType
from app.models.task_history import TaskHistory as TaskHistoryModel
from app.schemas.task_schema import (
    Comment,
    CommentCreate,
    StatusTransition,
    TaskCreate,
    TaskHistory,
    TaskUpdate,
)
from app.services.hierarchical_id_service import HierarchicalIdService
from app.services.tdd_hook_service import TDDHookService


class TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.hierarchical_id_service = HierarchicalIdService(db)
        self.tdd_hook_service = TDDHookService(db)

    def create_task(self, task: TaskCreate) -> Task:
        """タスクを作成"""
        # 親タスクを取得
        parent = None
        if task.parent_id:
            parent = self.hierarchical_id_service.get_parent_by_id(task.parent_id)
            if not parent:
                raise ValueError(f"Parent task with id {task.parent_id} not found")

        # 階層IDを生成
        hierarchical_id = self.hierarchical_id_service.generate_hierarchical_id(
            parent, task.type
        )

        # タスクを作成
        task_data = task.model_dump()
        task_data["hierarchical_id"] = hierarchical_id
        db_task = Task(**task_data)

        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task

    def get_tasks(self) -> List[Task]:
        """全タスクを取得"""
        return self.db.query(Task).all()

    def get_task(self, task_id: int) -> Optional[Task]:
        """IDでタスクを取得"""
        return self.db.query(Task).filter(Task.id == task_id).first()

    def update_task(self, task_id: int, task_update: TaskUpdate) -> Optional[Task]:
        """タスクを更新"""
        db_task = self.get_task(task_id)
        if not db_task:
            return None

        update_data = task_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_task, field, value)

        # updated_atを明示的に設定
        from datetime import datetime

        db_task.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(db_task)
        return db_task

    def delete_task(self, task_id: int) -> bool:
        """タスクを削除"""
        db_task = self.get_task(task_id)
        if not db_task:
            return False

        self.db.delete(db_task)
        self.db.commit()
        return True

    # 階層ナビゲーション用メソッド
    def get_requirements_summary(
        self, offset: int, limit: int, q: Optional[str], status: Optional[str]
    ) -> List[Task]:
        """要件一覧（軽量）"""
        query = self.db.query(Task).filter(Task.type == TaskType.requirement)

        if q:
            query = query.filter(Task.title.contains(q))
        if status:
            query = query.filter(Task.status == status)

        return query.offset(offset).limit(limit).all()

    def get_child_tasks(self, parent_id: int, task_type: TaskType) -> List[Task]:
        """子タスク一覧"""
        return (
            self.db.query(Task)
            .filter(Task.parent_id == parent_id, Task.type == task_type)
            .all()
        )

    def search_tasks(
        self,
        type: Optional[str],
        status: Optional[str],
        parent_id: Optional[int],
        q: Optional[str],
        sort: str,
        order: str,
        offset: int,
        limit: int,
    ) -> List[Task]:
        """タスク検索・フィルタ"""
        query = self.db.query(Task)

        if type:
            query = query.filter(Task.type == type)
        if status:
            query = query.filter(Task.status == status)
        if parent_id:
            query = query.filter(Task.parent_id == parent_id)
        if q:
            query = query.filter(
                or_(Task.title.contains(q), Task.description.contains(q))
            )

        # ソート
        if sort == "created_at":
            sort_column = Task.created_at
        elif sort == "updated_at":
            sort_column = Task.updated_at
        elif sort == "title":
            sort_column = Task.title
        else:
            sort_column = Task.created_at

        if order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        return query.offset(offset).limit(limit).all()

    # 状態遷移メソッド
    def transition_status(self, task_id: int, transition: StatusTransition) -> Task:
        """状態遷移（ガード付き）"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError("Task not found")

        # 状態遷移の妥当性をチェック
        if not self._is_valid_transition(task.status, transition.to_status):
            raise ValueError(
                f"Invalid transition from {task.status} to {transition.to_status}"
            )

        # 履歴を記録
        self._add_history(
            task_id,
            "status_change",
            task.status,
            transition.to_status,
            transition.reason,
        )

        # 状態を更新
        old_status = task.status
        task.status = transition.to_status

        # updated_atを明示的に設定
        from datetime import datetime

        task.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(task)

        # TDDフックを実行
        try:
            self.tdd_hook_service.handle_status_transition(
                task, old_status, transition.to_status, transition.reason
            )
        except Exception as e:
            # TDDフックのエラーは状態遷移を阻害しない
            import logging

            logging.error(f"TDD Hook error for task {task.hierarchical_id}: {str(e)}")

        return task

    def _is_valid_transition(self, from_status: str, to_status: str) -> bool:
        """状態遷移の妥当性をチェック"""
        valid_transitions = {
            "not_started": ["in_progress", "blocked"],
            "in_progress": ["review_pending", "blocked", "completed"],
            "review_pending": ["revising", "completed"],
            "revising": ["review_pending", "in_progress"],
            "blocked": ["not_started", "in_progress"],
            "completed": [],  # 完了状態からは遷移不可
        }
        return to_status in valid_transitions.get(from_status, [])

    def _add_history(
        self,
        task_id: int,
        event_type: str,
        from_status: Optional[str],
        to_status: Optional[str],
        note: Optional[str],
    ):
        """履歴を追加"""
        history = TaskHistoryModel(
            task_id=task_id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            note=note,
            changed_by="system",
        )
        self.db.add(history)
        self.db.commit()

    # コメント・履歴メソッド
    def add_comment(self, task_id: int, comment: CommentCreate) -> Comment:
        """コメント追加"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError("Task not found")

        db_comment = CommentModel(
            task_id=task_id, type=comment.type, body=comment.body, created_by="system"
        )
        self.db.add(db_comment)
        self.db.commit()
        self.db.refresh(db_comment)

        return Comment(
            id=db_comment.id,
            task_id=db_comment.task_id,
            type=db_comment.type,
            body=db_comment.body,
            created_by=db_comment.created_by,
            created_at=db_comment.created_at,
        )

    def get_comments(self, task_id: int, offset: int, limit: int) -> List[Comment]:
        """コメント一覧"""
        comments = (
            self.db.query(CommentModel)
            .filter(CommentModel.task_id == task_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            Comment(
                id=comment.id,
                task_id=comment.task_id,
                type=comment.type,
                body=comment.body,
                created_by=comment.created_by,
                created_at=comment.created_at,
            )
            for comment in comments
        ]

    def get_history(self, task_id: int, offset: int, limit: int) -> List[TaskHistory]:
        """履歴取得"""
        history_records = (
            self.db.query(TaskHistoryModel)
            .filter(TaskHistoryModel.task_id == task_id)
            .order_by(desc(TaskHistoryModel.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            TaskHistory(
                id=record.id,
                task_id=record.task_id,
                event_type=record.event_type,
                from_status=record.from_status,
                to_status=record.to_status,
                note=record.note,
                changed_by=record.changed_by,
                created_at=record.created_at,
            )
            for record in history_records
        ]

    def get_task_by_hierarchical_id(self, hierarchical_id: str) -> Optional[Task]:
        """階層IDでタスクを取得"""
        return (
            self.db.query(Task).filter(Task.hierarchical_id == hierarchical_id).first()
        )

    def get_task_tree(self, hierarchical_id: str, depth: int = 1) -> Dict[str, Any]:
        """タスクツリーを取得"""
        task = self.get_task_by_hierarchical_id(hierarchical_id)
        if not task:
            return {}

        def build_tree(node: Task, current_depth: int) -> Dict[str, Any]:
            if current_depth <= 0:
                return {}

            tree = {
                "hierarchical_id": node.hierarchical_id,
                "title": node.title,
                "type": node.type,
                "status": node.status,
                "children": [],
            }

            if current_depth > 1:
                for child in node.children:
                    child_tree = build_tree(child, current_depth - 1)
                    if child_tree:
                        tree["children"].append(child_tree)

            return tree

        return build_tree(task, depth)
