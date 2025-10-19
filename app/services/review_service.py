from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from app.models.review import Review, ReviewComment, ReviewResponse, ReviewStatus, ReviewType
from app.schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewStatusUpdate, ReviewCommentCreate, ReviewResponseCreate,
    ReviewDetail, ReviewSummary, ReviewTimeline, ReviewStatistics
)
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta


class ReviewService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_review(self, task_id: int, review: ReviewCreate) -> Review:
        """レビューを作成"""
        db_review = Review(
            task_id=task_id,
            **review.model_dump()
        )
        self.db.add(db_review)
        self.db.commit()
        self.db.refresh(db_review)
        return db_review
    
    def get_review(self, review_id: int) -> Optional[Review]:
        """レビューを取得"""
        return self.db.query(Review).filter(Review.id == review_id).first()
    
    def get_reviews_by_task(self, task_id: int) -> List[Review]:
        """タスクのレビュー一覧を取得"""
        return self.db.query(Review).filter(Review.task_id == task_id).all()
    
    def update_review(self, review_id: int, review_update: ReviewUpdate) -> Optional[Review]:
        """レビューを更新"""
        db_review = self.get_review(review_id)
        if not db_review:
            return None
        
        update_data = review_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_review, field, value)
        
        # updated_atを明示的に設定
        db_review.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_review)
        return db_review
    
    def update_review_status(self, review_id: int, status_update: ReviewStatusUpdate) -> Optional[Review]:
        """レビューの状態を更新"""
        db_review = self.get_review(review_id)
        if not db_review:
            return None
        
        old_status = db_review.status
        db_review.status = status_update.status
        
        # 状態に応じて日時を設定
        now = datetime.utcnow()
        if status_update.status == ReviewStatus.in_progress and old_status == ReviewStatus.pending:
            db_review.review_started_at = now
        elif status_update.status == ReviewStatus.completed and old_status == ReviewStatus.in_progress:
            db_review.review_completed_at = now
        elif status_update.status == ReviewStatus.completed and old_status == ReviewStatus.pending:
            # 直接完了の場合
            db_review.review_started_at = now
            db_review.review_completed_at = now
        
        if status_update.review_notes:
            db_review.review_notes = status_update.review_notes
        
        # updated_atを明示的に設定
        db_review.updated_at = now
        
        self.db.commit()
        self.db.refresh(db_review)
        return db_review
    
    def add_review_comment(self, review_id: int, comment: ReviewCommentCreate) -> ReviewComment:
        """レビューコメントを追加"""
        db_comment = ReviewComment(
            review_id=review_id,
            **comment.model_dump()
        )
        self.db.add(db_comment)
        self.db.commit()
        self.db.refresh(db_comment)
        return db_comment
    
    def get_review_comments(self, review_id: int) -> List[ReviewComment]:
        """レビューのコメント一覧を取得"""
        return self.db.query(ReviewComment).filter(ReviewComment.review_id == review_id).all()
    
    def add_review_response(self, review_id: int, response: ReviewResponseCreate) -> ReviewResponse:
        """レビュー対応を追加"""
        db_response = ReviewResponse(
            review_id=review_id,
            **response.model_dump()
        )
        self.db.add(db_response)
        self.db.commit()
        self.db.refresh(db_response)
        return db_response
    
    def get_review_responses(self, review_id: int) -> List[ReviewResponse]:
        """レビューの対応一覧を取得"""
        return self.db.query(ReviewResponse).filter(ReviewResponse.review_id == review_id).all()
    
    def complete_review_response(self, review_id: int, response_id: int) -> Optional[ReviewResponse]:
        """レビュー対応を完了"""
        db_response = self.db.query(ReviewResponse).filter(
            ReviewResponse.id == response_id,
            ReviewResponse.review_id == review_id
        ).first()
        
        if not db_response:
            return None
        
        db_response.response_completed_at = datetime.utcnow()
        
        # レビューの対応完了日時も更新
        db_review = self.get_review(review_id)
        if db_review:
            db_review.response_completed_at = datetime.utcnow()
            db_review.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_response)
        return db_response
    
    def get_review_detail(self, review_id: int) -> Optional[ReviewDetail]:
        """レビューの詳細情報を取得"""
        db_review = self.get_review(review_id)
        if not db_review:
            return None
        
        # コメントとレスポンスを取得
        comments = self.get_review_comments(review_id)
        responses = self.get_review_responses(review_id)
        
        return ReviewDetail(
            **db_review.__dict__,
            comments=comments,
            responses=responses
        )
    
    def get_review_timeline(self, review_id: int) -> Optional[ReviewTimeline]:
        """レビューのタイムライン情報を取得"""
        db_review = self.get_review(review_id)
        if not db_review:
            return None
        
        # 期間を計算
        review_duration = None
        response_duration = None
        total_duration = None
        
        if db_review.review_started_at and db_review.review_completed_at:
            review_duration = int((db_review.review_completed_at - db_review.review_started_at).total_seconds())
        
        if db_review.review_completed_at and db_review.response_completed_at:
            response_duration = int((db_review.response_completed_at - db_review.review_completed_at).total_seconds())
        
        if db_review.created_at and db_review.response_completed_at:
            total_duration = int((db_review.response_completed_at - db_review.created_at).total_seconds())
        elif db_review.created_at and db_review.review_completed_at:
            total_duration = int((db_review.review_completed_at - db_review.created_at).total_seconds())
        
        return ReviewTimeline(
            review_id=db_review.id,
            task_id=db_review.task_id,
            review_type=db_review.review_type,
            status=db_review.status,
            title=db_review.title,
            reviewer=db_review.reviewer,
            created_at=db_review.created_at,
            review_started_at=db_review.review_started_at,
            review_completed_at=db_review.review_completed_at,
            response_completed_at=db_review.response_completed_at,
            review_duration=review_duration,
            response_duration=response_duration,
            total_duration=total_duration
        )
    
    def get_review_statistics(self, task_id: Optional[int] = None) -> ReviewStatistics:
        """レビュー統計情報を取得"""
        query = self.db.query(Review)
        if task_id:
            query = query.filter(Review.task_id == task_id)
        
        reviews = query.all()
        
        # 基本統計
        total_reviews = len(reviews)
        pending_reviews = len([r for r in reviews if r.status == ReviewStatus.pending])
        in_progress_reviews = len([r for r in reviews if r.status == ReviewStatus.in_progress])
        completed_reviews = len([r for r in reviews if r.status == ReviewStatus.completed])
        rejected_reviews = len([r for r in reviews if r.status == ReviewStatus.rejected])
        cancelled_reviews = len([r for r in reviews if r.status == ReviewStatus.cancelled])
        
        # 平均期間計算
        completed_reviews_with_duration = [r for r in reviews if r.review_started_at and r.review_completed_at]
        avg_review_duration = None
        if completed_reviews_with_duration:
            durations = [(r.review_completed_at - r.review_started_at).total_seconds() for r in completed_reviews_with_duration]
            avg_review_duration = sum(durations) / len(durations)
        
        response_reviews_with_duration = [r for r in reviews if r.review_completed_at and r.response_completed_at]
        avg_response_duration = None
        if response_reviews_with_duration:
            durations = [(r.response_completed_at - r.review_completed_at).total_seconds() for r in response_reviews_with_duration]
            avg_response_duration = sum(durations) / len(durations)
        
        total_reviews_with_duration = [r for r in reviews if r.created_at and r.response_completed_at]
        avg_total_duration = None
        if total_reviews_with_duration:
            durations = [(r.response_completed_at - r.created_at).total_seconds() for r in total_reviews_with_duration]
            avg_total_duration = sum(durations) / len(durations)
        
        # レビュータイプ別統計
        review_type_stats = {}
        for review_type in ReviewType:
            type_reviews = [r for r in reviews if r.review_type == review_type]
            review_type_stats[review_type.value] = {
                "total": len(type_reviews),
                "pending": len([r for r in type_reviews if r.status == ReviewStatus.pending]),
                "in_progress": len([r for r in type_reviews if r.status == ReviewStatus.in_progress]),
                "completed": len([r for r in type_reviews if r.status == ReviewStatus.completed]),
                "rejected": len([r for r in type_reviews if r.status == ReviewStatus.rejected]),
                "cancelled": len([r for r in type_reviews if r.status == ReviewStatus.cancelled])
            }
        
        return ReviewStatistics(
            total_reviews=total_reviews,
            pending_reviews=pending_reviews,
            in_progress_reviews=in_progress_reviews,
            completed_reviews=completed_reviews,
            rejected_reviews=rejected_reviews,
            cancelled_reviews=cancelled_reviews,
            avg_review_duration=avg_review_duration,
            avg_response_duration=avg_response_duration,
            avg_total_duration=avg_total_duration,
            review_type_stats=review_type_stats
        )
    
    def search_reviews(self, status: Optional[ReviewStatus] = None, 
                      review_type: Optional[ReviewType] = None,
                      reviewer: Optional[str] = None,
                      task_id: Optional[int] = None,
                      sort: str = "created_at",
                      order: str = "desc",
                      offset: int = 0,
                      limit: int = 50) -> List[ReviewSummary]:
        """レビューを検索"""
        query = self.db.query(Review)
        
        if status:
            query = query.filter(Review.status == status)
        if review_type:
            query = query.filter(Review.review_type == review_type)
        if reviewer:
            query = query.filter(Review.reviewer.contains(reviewer))
        if task_id:
            query = query.filter(Review.task_id == task_id)
        
        # ソート
        if sort == "created_at":
            sort_column = Review.created_at
        elif sort == "updated_at":
            sort_column = Review.updated_at
        elif sort == "review_started_at":
            sort_column = Review.review_started_at
        elif sort == "review_completed_at":
            sort_column = Review.review_completed_at
        else:
            sort_column = Review.created_at
        
        if order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        reviews = query.offset(offset).limit(limit).all()
        
        return [ReviewSummary.model_validate(review) for review in reviews]
