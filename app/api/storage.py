from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.cas_service import CASService
from app.services.git_service import GitService

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/paths")
def get_storage_paths():
    """ストレージパス情報を取得"""
    return {
        "cas_root": str(settings.get_cas_root_path()),
        "file_storage_root": str(settings.get_file_storage_root()),
        "git_repo_path": str(settings.get_git_repo_path()),
        "cas_uri_prefix": "cas://sha256/",
        "git_uri_prefix": "git://",
    }


@router.get("/cas/{sha256_hash}/path")
def get_cas_file_path(sha256_hash: str, db: Session = Depends(get_db)):
    """CASファイルの格納パスを取得"""
    cas_service = CASService(db)
    artifact_info = cas_service.get_artifact_info(sha256_hash)

    if not artifact_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found"
        )

    return {
        "sha256": sha256_hash,
        "cas_path": artifact_info["cas_path"],
        "cas_uri": artifact_info["cas_uri"],
        "media_type": artifact_info["media_type"],
        "bytes_size": artifact_info["bytes_size"],
    }


@router.get("/git/{hierarchical_id}/path")
def get_git_task_path(hierarchical_id: str):
    """Gitタスクパスを取得"""
    git_service = GitService()

    try:
        task_path = git_service.get_task_path(hierarchical_id)
        outline_path = git_service.get_outline_path(hierarchical_id)
        spec_path = git_service.get_spec_path(hierarchical_id)

        return {
            "hierarchical_id": hierarchical_id,
            "task_path": str(task_path),
            "outline_path": str(outline_path),
            "spec_path": str(spec_path),
            "outline_uri": git_service.get_git_uri(hierarchical_id, "outline"),
            "spec_uri": git_service.get_git_uri(hierarchical_id, "spec"),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/git/{hierarchical_id}/files")
def get_git_task_files(hierarchical_id: str):
    """Gitタスクファイル一覧を取得"""
    git_service = GitService()

    try:
        files = git_service.list_task_files(hierarchical_id)
        return {"hierarchical_id": hierarchical_id, "files": files, "count": len(files)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/git/{hierarchical_id}/outline")
def create_git_outline(hierarchical_id: str, outline_data: Dict[str, Any]):
    """Gitアウトラインファイルを作成"""
    git_service = GitService()

    try:
        success = git_service.create_outline_file(hierarchical_id, outline_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create outline file",
            )

        outline_uri = git_service.get_git_uri(hierarchical_id, "outline")
        return {
            "hierarchical_id": hierarchical_id,
            "outline_uri": outline_uri,
            "message": "Outline file created successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/git/{hierarchical_id}/outline")
def get_git_outline(hierarchical_id: str):
    """Gitアウトラインファイルを取得"""
    git_service = GitService()

    try:
        outline_data = git_service.get_outline_file(hierarchical_id)
        if outline_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Outline file not found"
            )

        outline_uri = git_service.get_git_uri(hierarchical_id, "outline")
        return {
            "hierarchical_id": hierarchical_id,
            "outline_uri": outline_uri,
            "outline_data": outline_data,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/git/{hierarchical_id}/spec")
def create_git_spec(hierarchical_id: str, content: str):
    """Git仕様ファイルを作成"""
    git_service = GitService()

    try:
        success = git_service.create_spec_file(hierarchical_id, content)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create spec file",
            )

        spec_uri = git_service.get_git_uri(hierarchical_id, "spec")
        return {
            "hierarchical_id": hierarchical_id,
            "spec_uri": spec_uri,
            "message": "Spec file created successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/git/{hierarchical_id}/spec")
def get_git_spec(hierarchical_id: str):
    """Git仕様ファイルを取得"""
    git_service = GitService()

    try:
        content = git_service.get_spec_file(hierarchical_id)
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Spec file not found"
            )

        spec_uri = git_service.get_git_uri(hierarchical_id, "spec")
        return {
            "hierarchical_id": hierarchical_id,
            "spec_uri": spec_uri,
            "content": content,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/git/init")
def initialize_git_repo():
    """Gitリポジトリを初期化"""
    git_service = GitService()

    success = git_service.initialize_git_repo()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize git repository",
        )

    return {
        "message": "Git repository initialized successfully",
        "git_root": str(settings.get_git_repo_path()),
    }


@router.post("/git/commit")
def commit_git_changes(message: str = "Auto commit"):
    """Git変更をコミット"""
    git_service = GitService()

    success = git_service.commit_changes(message)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to commit changes",
        )

    return {
        "message": f"Changes committed successfully: {message}",
        "git_root": str(settings.get_git_repo_path()),
    }


@router.get("/status")
def get_storage_status():
    """ストレージ状態を取得"""
    cas_root = settings.get_cas_root_path()
    git_root = settings.get_git_repo_path()
    file_storage_root = settings.get_file_storage_root()

    # ディレクトリの存在確認
    cas_exists = cas_root.exists()
    git_exists = git_root.exists()
    file_storage_exists = file_storage_root.exists()

    # ファイル数の確認
    cas_file_count = 0
    if cas_exists:
        cas_file_count = len(list(cas_root.rglob("*")))

    git_file_count = 0
    if git_exists:
        git_file_count = len(list(git_root.rglob("*")))

    return {
        "cas_root": {
            "path": str(cas_root),
            "exists": cas_exists,
            "file_count": cas_file_count,
        },
        "git_root": {
            "path": str(git_root),
            "exists": git_exists,
            "file_count": git_file_count,
            "is_git_repo": (git_root / ".git").exists(),
        },
        "file_storage_root": {
            "path": str(file_storage_root),
            "exists": file_storage_exists,
        },
    }
