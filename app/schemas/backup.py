from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BackupCreate(BaseModel):
    """バックアップ作成リクエスト"""
    backup_name: Optional[str] = Field(None, description="バックアップ名（指定しない場合は自動生成）")


class BackupResponse(BaseModel):
    """バックアップ作成レスポンス"""
    model_config = ConfigDict(from_attributes=True)
    
    backup_name: str
    backup_path: str
    created_at: str
    status: str


class BackupInfo(BaseModel):
    """バックアップ情報"""
    model_config = ConfigDict(from_attributes=True)
    
    backup_name: str
    backup_path: str
    size: int
    created_at: Optional[str] = None
    backup_type: str = "full"
    database_url: Optional[str] = None
    version: str = "1.0.0"
    files: List[Dict[str, Any]] = []


class BackupList(BaseModel):
    """バックアップ一覧"""
    model_config = ConfigDict(from_attributes=True)
    
    backup_name: str
    created_at: Optional[str] = None
    backup_type: str = "full"
    size: int


class BackupRestore(BaseModel):
    """バックアップ復元リクエスト"""
    backup_name: str = Field(..., description="復元するバックアップ名")


class BackupRestoreResponse(BaseModel):
    """バックアップ復元レスポンス"""
    model_config = ConfigDict(from_attributes=True)
    
    backup_name: str
    status: str
    restored_at: Optional[str] = None
    error: Optional[str] = None


class BackupDeleteResponse(BaseModel):
    """バックアップ削除レスポンス"""
    model_config = ConfigDict(from_attributes=True)
    
    backup_name: str
    status: str
    deleted_at: Optional[str] = None
    error: Optional[str] = None


class BackupCleanup(BaseModel):
    """バックアップクリーンアップリクエスト"""
    days_to_keep: int = Field(30, ge=1, le=365, description="保持する日数（1-365日）")


class BackupCleanupResponse(BaseModel):
    """バックアップクリーンアップレスポンス"""
    model_config = ConfigDict(from_attributes=True)
    
    deleted_count: int
    errors: List[str] = []
    status: str


class BackupStatistics(BaseModel):
    """バックアップ統計情報"""
    model_config = ConfigDict(from_attributes=True)
    
    total_backups: int
    total_size: int
    oldest_backup: Optional[str] = None
    newest_backup: Optional[str] = None
    backup_types: Dict[str, int] = {}


class BackupFile(BaseModel):
    """バックアップファイル情報"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    path: str
    size: int
    modified: str
