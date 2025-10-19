import hashlib
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.artifact_model import Artifact, TaskArtifactLink

logger = logging.getLogger(__name__)


class CASService:
    def __init__(self, db: Session):
        self.db = db
        self.cas_root = settings.get_cas_root_path()
        self.cas_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"CAS root path: {self.cas_root}")

    def store_artifact(
        self,
        content: bytes,
        media_type: str,
        source_task_hid: Optional[str] = None,
        purpose: Optional[str] = None,
    ) -> str:
        """アーティファクトをCASに格納し、SHA-256ハッシュを返す"""
        # SHA-256ハッシュを計算
        sha256_hash = hashlib.sha256(content).hexdigest()

        # 既に存在するかチェック
        existing_artifact = (
            self.db.query(Artifact).filter(Artifact.sha256 == sha256_hash).first()
        )
        if existing_artifact:
            logger.info(f"Artifact with SHA-256 {sha256_hash} already exists")
            return sha256_hash

        # CASディレクトリ構造を作成
        cas_path = self._get_cas_path(sha256_hash)
        cas_path.parent.mkdir(parents=True, exist_ok=True)

        # ファイルを格納
        with open(cas_path, "wb") as f:
            f.write(content)

        # データベースに記録
        artifact = Artifact(
            sha256=sha256_hash,
            media_type=media_type,
            bytes_size=len(content),
            source_task_hid=source_task_hid,
            purpose=purpose,
        )
        self.db.add(artifact)
        self.db.commit()

        logger.info(f"Stored artifact with SHA-256 {sha256_hash} at {cas_path}")
        return sha256_hash

    def retrieve_artifact(self, sha256_hash: str) -> Optional[bytes]:
        """SHA-256ハッシュからアーティファクトを取得"""
        cas_path = self._get_cas_path(sha256_hash)

        if not cas_path.exists():
            logger.warning(f"Artifact with SHA-256 {sha256_hash} not found in CAS")
            return None

        with open(cas_path, "rb") as f:
            return f.read()

    def get_artifact_info(self, sha256_hash: str) -> Optional[Dict[str, Any]]:
        """アーティファクトの情報を取得"""
        artifact = (
            self.db.query(Artifact).filter(Artifact.sha256 == sha256_hash).first()
        )
        if not artifact:
            return None

        return {
            "sha256": artifact.sha256,
            "media_type": artifact.media_type,
            "bytes_size": artifact.bytes_size,
            "created_at": artifact.created_at,
            "source_task_hid": artifact.source_task_hid,
            "purpose": artifact.purpose,
            "cas_uri": f"cas://sha256/{sha256_hash[:2]}/{sha256_hash}",
            "cas_path": str(self._get_cas_path(sha256_hash)),
        }

    def link_artifact_to_task(self, task_hid: str, sha256_hash: str, role: str) -> bool:
        """アーティファクトをタスクにリンク"""
        artifact = (
            self.db.query(Artifact).filter(Artifact.sha256 == sha256_hash).first()
        )
        if not artifact:
            logger.error(f"Artifact with SHA-256 {sha256_hash} not found")
            return False

        # 既存のリンクをチェック
        existing_link = (
            self.db.query(TaskArtifactLink)
            .filter(
                TaskArtifactLink.task_hid == task_hid,
                TaskArtifactLink.artifact_id == artifact.id,
                TaskArtifactLink.role == role,
            )
            .first()
        )

        if existing_link:
            logger.info(
                f"Link already exists for task {task_hid} and artifact {sha256_hash} with role {role}"
            )
            return True

        # 新しいリンクを作成
        link = TaskArtifactLink(task_hid=task_hid, artifact_id=artifact.id, role=role)
        self.db.add(link)
        self.db.commit()

        logger.info(
            f"Linked artifact {sha256_hash} to task {task_hid} with role {role}"
        )
        return True

    def get_task_artifacts(self, task_hid: str, role: Optional[str] = None) -> list:
        """タスクに関連するアーティファクトを取得"""
        query = self.db.query(TaskArtifactLink).filter(
            TaskArtifactLink.task_hid == task_hid
        )

        if role:
            query = query.filter(TaskArtifactLink.role == role)

        links = query.all()
        artifacts = []

        for link in links:
            artifact_info = self.get_artifact_info(link.artifact.sha256)
            if artifact_info:
                artifact_info["role"] = link.role
                artifact_info["link_id"] = link.id
                artifacts.append(artifact_info)

        return artifacts

    def _get_cas_path(self, sha256_hash: str) -> Path:
        """CASパスを生成"""
        return self.cas_root / "sha256" / sha256_hash[:2] / sha256_hash

    def get_cas_uri(self, sha256_hash: str) -> str:
        """CAS URIを生成"""
        return f"cas://sha256/{sha256_hash[:2]}/{sha256_hash}"

    def delete_artifact(self, sha256_hash: str) -> bool:
        """アーティファクトを削除"""
        artifact = (
            self.db.query(Artifact).filter(Artifact.sha256 == sha256_hash).first()
        )
        if not artifact:
            return False

        # ファイルを削除
        cas_path = self._get_cas_path(sha256_hash)
        if cas_path.exists():
            cas_path.unlink()

        # リンクを削除
        self.db.query(TaskArtifactLink).filter(
            TaskArtifactLink.artifact_id == artifact.id
        ).delete()

        # アーティファクトを削除
        self.db.delete(artifact)
        self.db.commit()

        logger.info(f"Deleted artifact with SHA-256 {sha256_hash}")
        return True
