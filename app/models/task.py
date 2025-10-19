from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import event
from app.core.database import Base
import enum
from datetime import datetime


class TaskType(str, enum.Enum):
    requirement = "requirement"
    task = "task"
    subtask = "subtask"


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    hierarchical_id = Column(String(255), unique=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(TaskType), nullable=False)
    status = Column(String(50), default="not_started")
    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーションシップ
    parent = relationship("Task", remote_side=[id], backref="children")


@event.listens_for(Task, 'before_update')
def update_updated_at(mapper, connection, target):
    """タスクが更新される前にupdated_atを自動設定"""
    target.updated_at = datetime.utcnow()
