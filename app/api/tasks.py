from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.task import TaskType
from app.schemas.task import (
    Comment,
    CommentCreate,
    RequirementCreate,
    RequirementSummary,
    StatusTransition,
    SubtaskSummary,
    Task,
    TaskCreate,
    TaskHistory,
    TaskSearchParams,
    TaskSummary,
    TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])
requirements_router = APIRouter(prefix="/requirements", tags=["requirements"])


@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """タスクを作成"""
    task_service = TaskService(db)
    try:
        return task_service.create_task(task)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/requirements/", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_requirement(requirement: RequirementCreate, db: Session = Depends(get_db)):
    """要件を作成"""
    task_create = TaskCreate(
        **requirement.model_dump(), type=TaskType.requirement, parent_id=None
    )
    task_service = TaskService(db)
    try:
        return task_service.create_task(task_create)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[Task])
def get_tasks(db: Session = Depends(get_db)):
    """全タスクを取得"""
    task_service = TaskService(db)
    return task_service.get_tasks()


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """IDでタスクを取得"""
    task_service = TaskService(db)
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.put("/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """タスクを更新"""
    task_service = TaskService(db)
    task = task_service.update_task(task_id, task_update)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """タスクを削除"""
    task_service = TaskService(db)
    if not task_service.delete_task(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )


# 階層ナビゲーションAPI
@requirements_router.get("/", response_model=List[RequirementSummary])
def get_requirements(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """要件一覧（軽量）"""
    task_service = TaskService(db)
    return task_service.get_requirements_summary(offset, limit, q, status)


@requirements_router.get("/{req_id}", response_model=Task)
def get_requirement(req_id: int, db: Session = Depends(get_db)):
    """要件詳細"""
    task_service = TaskService(db)
    task = task_service.get_task(req_id)
    if not task or task.type != TaskType.requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found"
        )
    return task


@requirements_router.get("/{req_id}/tasks", response_model=List[TaskSummary])
def get_requirement_tasks(req_id: int, db: Session = Depends(get_db)):
    """要件の子タスク一覧"""
    task_service = TaskService(db)
    return task_service.get_child_tasks(req_id, TaskType.task)


@router.get("/{task_id}/subtasks", response_model=List[SubtaskSummary])
def get_task_subtasks(task_id: int, db: Session = Depends(get_db)):
    """タスクの子サブタスク一覧"""
    task_service = TaskService(db)
    return task_service.get_child_tasks(task_id, TaskType.subtask)


# 検索・フィルタAPI
@router.get("/search", response_model=List[TaskSummary])
def search_tasks(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    parent_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
    sort: str = Query("created_at"),
    order: str = Query("desc"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """タスク検索・フィルタ"""
    task_service = TaskService(db)
    return task_service.search_tasks(
        type=type,
        status=status,
        parent_id=parent_id,
        q=q,
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
    )


# 状態遷移API
@router.post("/{task_id}/transition", response_model=Task)
def transition_task_status(
    task_id: int, transition: StatusTransition, db: Session = Depends(get_db)
):
    """状態遷移（ガード付き）"""
    task_service = TaskService(db)
    try:
        return task_service.transition_status(task_id, transition)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# コメントAPI
@router.post(
    "/{task_id}/comments", response_model=Comment, status_code=status.HTTP_201_CREATED
)
def add_comment(task_id: int, comment: CommentCreate, db: Session = Depends(get_db)):
    """コメント追加"""
    task_service = TaskService(db)
    try:
        return task_service.add_comment(task_id, comment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{task_id}/comments", response_model=List[Comment])
def get_task_comments(
    task_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """タスクのコメント一覧"""
    task_service = TaskService(db)
    return task_service.get_comments(task_id, offset, limit)


# 履歴API
@router.get("/{task_id}/history", response_model=List[TaskHistory])
def get_task_history(
    task_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """履歴取得"""
    task_service = TaskService(db)
    return task_service.get_history(task_id, offset, limit)
