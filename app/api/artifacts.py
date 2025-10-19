import base64
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.task import Task, TaskType
from app.schemas.artifact import (
    ArtifactCreate,
    ArtifactInfo,
    ArtifactRetrieve,
    OutlineCard,
    TaskArtifactLink,
    TaskArtifactLinkCreate,
    TaskSummary,
    TaskSummaryCreate,
)
from app.services.cas_service import CASService
from app.services.task_service import TaskService

router = APIRouter(prefix="/artifacts", tags=["artifacts"])
summaries_router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.post("/", response_model=ArtifactInfo, status_code=status.HTTP_201_CREATED)
def store_artifact(artifact: ArtifactCreate, db: Session = Depends(get_db)):
    """アーティファクトをCASに格納"""
    try:
        # Base64デコード
        content = base64.b64decode(artifact.content)

        cas_service = CASService(db)
        sha256_hash = cas_service.store_artifact(
            content=content,
            media_type=artifact.media_type,
            source_task_hid=artifact.source_task_hid,
            purpose=artifact.purpose,
        )

        # アーティファクト情報を取得
        artifact_info = cas_service.get_artifact_info(sha256_hash)
        if not artifact_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve artifact info",
            )

        return artifact_info

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{sha256_hash}", response_model=ArtifactInfo)
def get_artifact_info(sha256_hash: str, db: Session = Depends(get_db)):
    """アーティファクト情報を取得"""
    cas_service = CASService(db)
    artifact_info = cas_service.get_artifact_info(sha256_hash)

    if not artifact_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found"
        )

    return artifact_info


@router.get("/{sha256_hash}/content")
def get_artifact_content(sha256_hash: str, db: Session = Depends(get_db)):
    """アーティファクトの内容を取得"""
    cas_service = CASService(db)
    content = cas_service.retrieve_artifact(sha256_hash)

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found"
        )

    # アーティファクト情報を取得してContent-Typeを設定
    artifact_info = cas_service.get_artifact_info(sha256_hash)
    media_type = (
        artifact_info["media_type"] if artifact_info else "application/octet-stream"
    )

    return {
        "content": base64.b64encode(content).decode("utf-8"),
        "media_type": media_type,
        "sha256": sha256_hash,
    }


@router.post(
    "/{sha256_hash}/link",
    response_model=TaskArtifactLink,
    status_code=status.HTTP_201_CREATED,
)
def link_artifact_to_task(
    sha256_hash: str, link_data: TaskArtifactLinkCreate, db: Session = Depends(get_db)
):
    """アーティファクトをタスクにリンク"""
    cas_service = CASService(db)

    success = cas_service.link_artifact_to_task(
        task_hid=link_data.sha256_hash,  # 実際にはtask_hidを渡すべき
        sha256_hash=sha256_hash,
        role=link_data.role,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to link artifact to task",
        )

    # リンク情報を取得
    artifacts = cas_service.get_task_artifacts(link_data.sha256_hash, link_data.role)
    if not artifacts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link not found"
        )

    return artifacts[0]


@router.get("/tasks/{task_hid}/artifacts", response_model=List[TaskArtifactLink])
def get_task_artifacts(
    task_hid: str, role: Optional[str] = Query(None), db: Session = Depends(get_db)
):
    """タスクに関連するアーティファクトを取得"""
    cas_service = CASService(db)
    artifacts = cas_service.get_task_artifacts(task_hid, role)

    return artifacts


@router.delete("/{sha256_hash}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artifact(sha256_hash: str, db: Session = Depends(get_db)):
    """アーティファクトを削除"""
    cas_service = CASService(db)

    success = cas_service.delete_artifact(sha256_hash)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found"
        )


# タスクサマリー管理API
@summaries_router.post(
    "/", response_model=TaskSummary, status_code=status.HTTP_201_CREATED
)
def create_task_summary(summary: TaskSummaryCreate, db: Session = Depends(get_db)):
    """タスクサマリーを作成"""
    from app.models.artifact_model import TaskSummary as TaskSummaryModel

    # 既存のサマリーをチェック
    existing = (
        db.query(TaskSummaryModel)
        .filter(TaskSummaryModel.task_hid == summary.task_hid)
        .first()
    )
    if existing:
        # 更新
        existing.summary_140 = summary.summary_140
        existing.acceptance_json = summary.acceptance_json
        db.commit()
        db.refresh(existing)
        return existing

    # 新規作成
    db_summary = TaskSummaryModel(
        task_hid=summary.task_hid,
        summary_140=summary.summary_140,
        acceptance_json=summary.acceptance_json,
    )
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)

    return db_summary


@summaries_router.get("/{task_hid}", response_model=TaskSummary)
def get_task_summary(task_hid: str, db: Session = Depends(get_db)):
    """タスクサマリーを取得"""
    from app.models.artifact_model import TaskSummary as TaskSummaryModel

    summary = (
        db.query(TaskSummaryModel).filter(TaskSummaryModel.task_hid == task_hid).first()
    )
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task summary not found"
        )

    return summary


@summaries_router.get("/{task_hid}/outline", response_model=OutlineCard)
def get_task_outline(task_hid: str, db: Session = Depends(get_db)):
    """タスクのアウトラインカードを取得"""
    from app.models.artifact_model import TaskSummary as TaskSummaryModel

    # タスク情報を取得
    task_service = TaskService(db)
    task = task_service.get_task_by_hierarchical_id(task_hid)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    # サマリーを取得
    summary = (
        db.query(TaskSummaryModel).filter(TaskSummaryModel.task_hid == task_hid).first()
    )

    # アーティファクトリンクを取得
    cas_service = CASService(db)
    artifacts = cas_service.get_task_artifacts(task_hid)

    # URIを構築
    uris = {}
    for artifact in artifacts:
        if artifact["role"] == "spec":
            uris["spec"] = artifact["cas_uri"]
        elif artifact["role"] == "test":
            uris["tests_dir"] = artifact["cas_uri"]
        elif artifact["role"] == "context":
            uris["context_pack"] = artifact["cas_uri"]

    # アウトラインカードを構築
    outline = OutlineCard(
        hierarchical_id=task_hid,
        title=task.title,
        summary=(
            summary.summary_140
            if summary
            else task.description[:140] if task.description else ""
        ),
        acceptance=summary.acceptance_json if summary else [],
        depends_on=[],  # 依存関係は別途実装
        uris=uris,
    )

    return outline
