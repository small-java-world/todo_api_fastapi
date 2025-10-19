from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.task import TaskType


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None


class TaskCreate(TaskBase):
    type: TaskType
    parent_id: Optional[int] = None


class RequirementCreate(TaskBase):
    """要件作成用のスキーマ（typeとparent_idは自動設定）"""

    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class Task(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hierarchical_id: str
    type: TaskType
    status: str = "not_started"
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# 軽量レスポンス用スキーマ
class TaskSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hierarchical_id: str
    title: str
    type: TaskType
    status: str
    parent_id: Optional[int] = None


class RequirementSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hierarchical_id: str
    title: str
    status: str


class SubtaskSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hierarchical_id: str
    title: str
    status: str
    parent_id: int


# 検索・フィルタ用スキーマ
class TaskSearchParams(BaseModel):
    type: Optional[str] = None
    status: Optional[str] = None
    parent_id: Optional[int] = None
    q: Optional[str] = None
    sort: str = "created_at"
    order: str = "desc"
    offset: int = 0
    limit: int = 50


# 状態遷移用スキーマ
class StatusTransition(BaseModel):
    from_status: str
    to_status: str
    reason: Optional[str] = None


# コメント用スキーマ
class CommentCreate(BaseModel):
    type: str  # "review" or "note"
    body: str


class Comment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    type: str
    body: str
    created_by: Optional[str] = None
    created_at: datetime


# 履歴用スキーマ
class TaskHistory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    event_type: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    note: Optional[str] = None
    changed_by: Optional[str] = None
    created_at: datetime


# 軽量化されたレスポンス用スキーマ
class TaskLightweight(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hierarchical_id: str
    type: TaskType
    title: str
    status: str
    updated_at: Optional[datetime] = None
    uri_outline: Optional[str] = None


class TaskDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hierarchical_id: str
    type: TaskType
    title: str
    description: Optional[str] = None
    status: str
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    uris: Optional[Dict[str, str]] = None
    links: Optional[List[Dict[str, str]]] = None
    comments: Optional[List[Comment]] = None
    history: Optional[List[TaskHistory]] = None


class TaskTree(BaseModel):
    hierarchical_id: str
    title: str
    type: TaskType
    status: str
    children: List["TaskTree"] = []


# 自己参照のための前方宣言
TaskTree.model_rebuild()
