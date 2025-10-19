from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.task import Task, TaskType
from typing import Optional
import time
import logging

logger = logging.getLogger(__name__)

class HierarchicalIdService:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_hierarchical_id(self, parent: Optional[Task], task_type: TaskType) -> str:
        """競合安全な階層ID生成"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                hierarchical_id = self._generate_hierarchical_id_internal(parent, task_type)
                # 一意性制約で競合を検出
                return hierarchical_id
            except IntegrityError as e:
                logger.warning(f"Hierarchical ID conflict on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to generate unique hierarchical ID after {max_retries} attempts")
                time.sleep(0.1 * (2 ** attempt))  # 指数バックオフ
        raise ValueError("Unexpected error in hierarchical ID generation")

    def _generate_hierarchical_id_internal(self, parent: Optional[Task], task_type: TaskType) -> str:
        """階層ID生成の内部ロジック"""
        if task_type == TaskType.requirement:
            # 要件の場合：REQ-001, REQ-002, ...
            count = self.db.query(Task).filter(Task.type == TaskType.requirement).count() + 1
            return f"REQ-{count:03d}"
        
        elif task_type == TaskType.task and parent:
            # タスクの場合：REQ-001.TSK-001, REQ-001.TSK-002, ...
            task_count = self.db.query(Task).filter(
                Task.parent_id == parent.id,
                Task.type == TaskType.task
            ).count() + 1
            return f"{parent.hierarchical_id}.TSK-{task_count:03d}"
        
        elif task_type == TaskType.subtask and parent:
            # サブタスクの場合：REQ-001.TSK-001.SUB-001, REQ-001.TSK-001.SUB-002, ...
            subtask_count = self.db.query(Task).filter(
                Task.parent_id == parent.id,
                Task.type == TaskType.subtask
            ).count() + 1
            return f"{parent.hierarchical_id}.SUB-{subtask_count:03d}"
        
        else:
            raise ValueError("Invalid combination of type and parent")
    
    def get_parent_by_id(self, parent_id: int) -> Optional[Task]:
        """親タスクを取得"""
        return self.db.query(Task).filter(Task.id == parent_id).first()
    
    def validate_parent_child_relationship(self, parent: Task, child_type: TaskType) -> bool:
        """親子関係の妥当性を検証"""
        if child_type == TaskType.task:
            return parent.type == TaskType.requirement
        elif child_type == TaskType.subtask:
            return parent.type == TaskType.task
        return False
    
    def check_circular_reference(self, task_id: int, new_parent_id: int) -> bool:
        """循環参照のチェック"""
        if task_id == new_parent_id:
            return True
        
        # 新しい親の祖先を辿って循環参照をチェック
        current_parent_id = new_parent_id
        visited = set()
        
        while current_parent_id is not None:
            if current_parent_id in visited:
                return True  # 循環参照発見
            if current_parent_id == task_id:
                return True  # 自分を祖先にしようとしている
            
            visited.add(current_parent_id)
            parent_task = self.db.query(Task).filter(Task.id == current_parent_id).first()
            current_parent_id = parent_task.parent_id if parent_task else None
        
        return False
