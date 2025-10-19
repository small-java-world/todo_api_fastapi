from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Artifact(Base):
    __tablename__ = "artifacts"
    
    id = Column(Integer, primary_key=True, index=True)
    sha256 = Column(String(64), unique=True, index=True, nullable=False)  # SHA-256ハッシュ
    media_type = Column(String(100), nullable=False)  # MIME type
    bytes_size = Column(BigInteger, nullable=False)  # ファイルサイズ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    source_task_hid = Column(String(255), nullable=True)  # 生成元タスクの階層ID
    purpose = Column(String(50), nullable=True)  # 用途: spec, test, build, log, patch, artifact
    
    # リレーションシップ
    task_links = relationship("TaskArtifactLink", back_populates="artifact")


class TaskArtifactLink(Base):
    __tablename__ = "task_artifact_links"
    
    id = Column(Integer, primary_key=True, index=True)
    task_hid = Column(String(255), nullable=False, index=True)  # タスクの階層ID
    artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=False)
    role = Column(String(50), nullable=False)  # spec, prompt, test, build, log, patch, artifact
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # リレーションシップ
    artifact = relationship("Artifact", back_populates="task_links")


class TaskSummary(Base):
    __tablename__ = "task_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    task_hid = Column(String(255), unique=True, nullable=False, index=True)  # タスクの階層ID
    summary_140 = Column(String(140), nullable=False)  # 140文字以内の要約
    acceptance_json = Column(Text, nullable=True)  # 受け入れ条件のJSON
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
