from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ReviewStatus(str, enum.Enum):
    pending = "pending"  # レビュー待ち
    in_progress = "in_progress"  # レビュー実施中
    completed = "completed"  # レビュー完了
    rejected = "rejected"  # レビュー却下
    cancelled = "cancelled"  # レビューキャンセル


class ReviewType(str, enum.Enum):
    code_review = "code_review"  # コードレビュー
    design_review = "design_review"  # 設計レビュー
    requirement_review = "requirement_review"  # 要件レビュー
    test_review = "test_review"  # テストレビュー
    document_review = "document_review"  # 文書レビュー


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    review_type = Column(Enum(ReviewType), nullable=False)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.pending)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    reviewer = Column(String(255), nullable=True)  # レビュアー
    review_notes = Column(Text, nullable=True)  # レビューコメント
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # レビュー開始日時
    review_started_at = Column(DateTime(timezone=True), nullable=True)
    # レビュー完了日時
    review_completed_at = Column(DateTime(timezone=True), nullable=True)
    # レビュー対応完了日時
    response_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # リレーションシップ
    task = relationship("Task", backref="reviews")


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    comment_type = Column(String(50), nullable=False)  # "question", "suggestion", "issue", "approval"
    content = Column(Text, nullable=False)
    line_number = Column(Integer, nullable=True)  # コード行番号（コードレビューの場合）
    file_path = Column(String(500), nullable=True)  # ファイルパス（コードレビューの場合）
    author = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # リレーションシップ
    review = relationship("Review", backref="comments")


class ReviewResponse(Base):
    __tablename__ = "review_responses"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    comment_id = Column(Integer, ForeignKey("review_comments.id"), nullable=True)  # 特定のコメントへの返信
    response_type = Column(String(50), nullable=False)  # "acknowledgment", "fix", "discussion", "rejection"
    content = Column(Text, nullable=False)
    author = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 対応完了日時
    response_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # リレーションシップ
    review = relationship("Review", backref="responses")
    comment = relationship("ReviewComment", backref="responses")
