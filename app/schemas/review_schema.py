from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.review import ReviewStatus, ReviewType


class ReviewBase(BaseModel):
    review_type: ReviewType
    title: str
    description: Optional[str] = None
    reviewer: Optional[str] = None


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    reviewer: Optional[str] = None
    review_notes: Optional[str] = None


class ReviewStatusUpdate(BaseModel):
    status: ReviewStatus
    review_notes: Optional[str] = None


class ReviewCommentCreate(BaseModel):
    comment_type: str  # "question", "suggestion", "issue", "approval"
    content: str
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    author: Optional[str] = None


class ReviewComment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    review_id: int
    comment_type: str
    content: str
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    author: Optional[str] = None
    created_at: datetime


class ReviewResponseCreate(BaseModel):
    comment_id: Optional[int] = None  # 特定のコメントへの返信
    response_type: str  # "acknowledgment", "fix", "discussion", "rejection"
    content: str
    author: Optional[str] = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    review_id: int
    comment_id: Optional[int] = None
    response_type: str
    content: str
    author: Optional[str] = None
    created_at: datetime
    response_completed_at: Optional[datetime] = None


class Review(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    status: ReviewStatus
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    review_started_at: Optional[datetime] = None
    review_completed_at: Optional[datetime] = None
    response_completed_at: Optional[datetime] = None


class ReviewDetail(Review):
    """レビューの詳細情報（コメントとレスポンスを含む）"""

    comments: Optional[List[ReviewComment]] = None
    responses: Optional[List[ReviewResponse]] = None


class ReviewSummary(BaseModel):
    """レビューのサマリー情報"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    review_type: ReviewType
    status: ReviewStatus
    title: str
    reviewer: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    review_started_at: Optional[datetime] = None
    review_completed_at: Optional[datetime] = None
    response_completed_at: Optional[datetime] = None


class ReviewTimeline(BaseModel):
    """レビューのタイムライン情報"""

    review_id: int
    task_id: int
    review_type: ReviewType
    status: ReviewStatus
    title: str
    reviewer: Optional[str] = None

    # タイムライン
    created_at: datetime
    review_started_at: Optional[datetime] = None
    review_completed_at: Optional[datetime] = None
    response_completed_at: Optional[datetime] = None

    # 期間計算
    review_duration: Optional[int] = None  # レビュー実施期間（秒）
    response_duration: Optional[int] = None  # レビュー対応期間（秒）
    total_duration: Optional[int] = None  # 総期間（秒）


class ReviewStatistics(BaseModel):
    """レビュー統計情報"""

    total_reviews: int
    pending_reviews: int
    in_progress_reviews: int
    completed_reviews: int
    rejected_reviews: int
    cancelled_reviews: int

    # 平均期間
    avg_review_duration: Optional[float] = None  # 平均レビュー実施期間（秒）
    avg_response_duration: Optional[float] = None  # 平均レビュー対応期間（秒）
    avg_total_duration: Optional[float] = None  # 平均総期間（秒）

    # レビュータイプ別統計
    review_type_stats: dict = {}
