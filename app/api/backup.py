from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.backup import (
    BackupCleanup,
    BackupCleanupResponse,
    BackupCreate,
    BackupDeleteResponse,
    BackupFile,
    BackupInfo,
    BackupList,
    BackupResponse,
    BackupRestore,
    BackupRestoreResponse,
    BackupStatistics,
)
from app.services.backup_service import BackupService

router = APIRouter(prefix="/backup", tags=["backup"])


@router.post("/", response_model=BackupResponse, status_code=status.HTTP_201_CREATED)
def create_backup(backup_data: BackupCreate, db: Session = Depends(get_db)):
    """データベースバックアップを作成"""
    backup_service = BackupService(db)
    try:
        result = backup_service.create_backup(backup_data.backup_name)
        if result["status"] == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )
        return BackupResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/", response_model=List[BackupList])
def list_backups(db: Session = Depends(get_db)):
    """バックアップ一覧を取得"""
    backup_service = BackupService(db)
    try:
        backups = backup_service.list_backups()
        return [BackupList(**backup) for backup in backups]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/statistics", response_model=BackupStatistics)
def get_backup_statistics(db: Session = Depends(get_db)):
    """バックアップ統計情報を取得"""
    backup_service = BackupService(db)
    try:
        backups = backup_service.list_backups()

        total_backups = len(backups)
        total_size = sum(backup.get("size", 0) for backup in backups)

        if backups:
            # 作成日時でソート
            sorted_backups = sorted(backups, key=lambda x: x.get("created_at", ""))
            oldest_backup = sorted_backups[0].get("created_at")
            newest_backup = sorted_backups[-1].get("created_at")
        else:
            oldest_backup = None
            newest_backup = None

        # バックアップタイプ別統計
        backup_types = {}
        for backup in backups:
            backup_type = backup.get("backup_type", "unknown")
            backup_types[backup_type] = backup_types.get(backup_type, 0) + 1

        return BackupStatistics(
            total_backups=total_backups,
            total_size=total_size,
            oldest_backup=oldest_backup,
            newest_backup=newest_backup,
            backup_types=backup_types,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{backup_name}", response_model=BackupInfo)
def get_backup_info(backup_name: str, db: Session = Depends(get_db)):
    """バックアップの詳細情報を取得"""
    backup_service = BackupService(db)
    try:
        result = backup_service.get_backup_info(backup_name)
        if result.get("status") == "failed":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=result["error"]
            )
        return BackupInfo(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{backup_name}/restore", response_model=BackupRestoreResponse)
def restore_backup(
    backup_name: str, restore_data: BackupRestore, db: Session = Depends(get_db)
):
    """バックアップからデータベースを復元"""
    backup_service = BackupService(db)
    try:
        result = backup_service.restore_backup(backup_name)
        if result["status"] == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )
        return BackupRestoreResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/{backup_name}", response_model=BackupDeleteResponse)
def delete_backup(backup_name: str, db: Session = Depends(get_db)):
    """バックアップを削除"""
    backup_service = BackupService(db)
    try:
        result = backup_service.delete_backup(backup_name)
        if result["status"] == "failed":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=result["error"]
            )
        return BackupDeleteResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/cleanup", response_model=BackupCleanupResponse)
def cleanup_old_backups(cleanup_data: BackupCleanup, db: Session = Depends(get_db)):
    """古いバックアップをクリーンアップ"""
    backup_service = BackupService(db)
    try:
        result = backup_service.cleanup_old_backups(cleanup_data.days_to_keep)
        return BackupCleanupResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{backup_name}/files", response_model=List[BackupFile])
def get_backup_files(backup_name: str, db: Session = Depends(get_db)):
    """バックアップ内のファイル一覧を取得"""
    backup_service = BackupService(db)
    try:
        result = backup_service.get_backup_info(backup_name)
        if result.get("status") == "failed":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=result["error"]
            )

        files = result.get("files", [])
        return [BackupFile(**file_info) for file_info in files]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{backup_name}/download")
def download_backup(backup_name: str, db: Session = Depends(get_db)):
    """バックアップをダウンロード（ZIP形式）"""
    import tempfile
    import zipfile

    from fastapi.responses import FileResponse

    backup_service = BackupService(db)
    try:
        result = backup_service.get_backup_info(backup_name)
        if result.get("status") == "failed":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=result["error"]
            )

        backup_path = result["backup_path"]

        # 一時ZIPファイルを作成
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in Path(backup_path).rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(Path(backup_path))
                        zipf.write(file_path, arcname)

            return FileResponse(
                path=temp_zip.name,
                filename=f"{backup_name}.zip",
                media_type="application/zip",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
