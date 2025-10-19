from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.task import TaskType
from app.schemas.task import TaskDetail, TaskLightweight, TaskTree
from app.services.cas_service import CASService
from app.services.task_service import TaskService

router = APIRouter(prefix="/tree", tags=["tree"])


@router.get("/{hierarchical_id}", response_model=TaskTree)
def get_task_tree(
    hierarchical_id: str,
    depth: int = Query(1, ge=1, le=5),
    db: Session = Depends(get_db),
):
    """タスクツリーを取得"""
    task_service = TaskService(db)
    tree = task_service.get_task_tree(hierarchical_id, depth)

    if not tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    return tree


@router.get("/", response_model=List[TaskLightweight])
def get_tasks_lightweight(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    parent_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
    sort: str = Query("updated_at"),
    order: str = Query("desc"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """軽量タスク一覧を取得"""
    task_service = TaskService(db)
    tasks = task_service.search_tasks(
        type=type,
        status=status,
        parent_id=parent_id,
        q=q,
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
    )

    # 軽量レスポンスに変換
    lightweight_tasks = []
    for task in tasks:
        # アウトラインURIを生成
        uri_outline = f"/summaries/{task.hierarchical_id}/outline"

        lightweight_task = TaskLightweight(
            id=task.id,
            hierarchical_id=task.hierarchical_id,
            type=task.type,
            title=task.title,
            status=task.status,
            updated_at=task.updated_at or task.created_at,
            uri_outline=uri_outline,
        )
        lightweight_tasks.append(lightweight_task)

    return lightweight_tasks


@router.get("/{hierarchical_id}/detail", response_model=TaskDetail)
def get_task_detail(
    hierarchical_id: str,
    expand: Optional[str] = Query(None),  # "comments,history,links"
    db: Session = Depends(get_db),
):
    """タスク詳細を取得（expand指定で段階取得）"""
    task_service = TaskService(db)
    task = task_service.get_task_by_hierarchical_id(hierarchical_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    # 基本情報
    detail = TaskDetail(
        id=task.id,
        hierarchical_id=task.hierarchical_id,
        type=task.type,
        title=task.title,
        description=task.description,
        status=task.status,
        parent_id=task.parent_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )

    # expand指定に応じて追加情報を取得
    if expand:
        expand_fields = [field.strip() for field in expand.split(",")]

        # URI情報を取得
        if "uris" in expand_fields:
            cas_service = CASService(db)
            artifacts = cas_service.get_task_artifacts(hierarchical_id)
            uris = {}
            for artifact in artifacts:
                if artifact["role"] == "spec":
                    uris["spec"] = artifact["cas_uri"]
                elif artifact["role"] == "test":
                    uris["tests_dir"] = artifact["cas_uri"]
                elif artifact["role"] == "context":
                    uris["context_pack"] = artifact["cas_uri"]
            detail.uris = uris

        # リンク情報を取得
        if "links" in expand_fields:
            cas_service = CASService(db)
            artifacts = cas_service.get_task_artifacts(hierarchical_id)
            links = []
            for artifact in artifacts:
                links.append({"role": artifact["role"], "uri": artifact["cas_uri"]})
            detail.links = links

        # コメントを取得
        if "comments" in expand_fields:
            comments = task_service.get_comments(task.id, 0, 50)
            detail.comments = comments

        # 履歴を取得
        if "history" in expand_fields:
            history = task_service.get_history(task.id, 0, 50)
            detail.history = history

    return detail


@router.get("/requirements/", response_model=List[TaskLightweight])
def get_requirements_lightweight(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """軽量要件一覧を取得"""
    task_service = TaskService(db)
    requirements = task_service.get_requirements_summary(offset, limit, q, status)

    # 軽量レスポンスに変換
    lightweight_requirements = []
    for req in requirements:
        uri_outline = f"/summaries/{req.hierarchical_id}/outline"

        lightweight_req = TaskLightweight(
            id=req.id,
            hierarchical_id=req.hierarchical_id,
            type=req.type,
            title=req.title,
            status=req.status,
            updated_at=req.updated_at or req.created_at,
            uri_outline=uri_outline,
        )
        lightweight_requirements.append(lightweight_req)

    return lightweight_requirements


@router.get("/{hierarchical_id}/children", response_model=List[TaskLightweight])
def get_task_children(
    hierarchical_id: str,
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """タスクの子要素を取得"""
    task_service = TaskService(db)
    task = task_service.get_task_by_hierarchical_id(hierarchical_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    children = []
    for child in task.children:
        if type is None or child.type == type:
            uri_outline = f"/summaries/{child.hierarchical_id}/outline"

            lightweight_child = TaskLightweight(
                id=child.id,
                hierarchical_id=child.hierarchical_id,
                type=child.type,
                title=child.title,
                status=child.status,
                updated_at=child.updated_at or child.created_at,
                uri_outline=uri_outline,
            )
            children.append(lightweight_child)

    return children
