from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.review import (
    Review, ReviewCreate, ReviewUpdate, ReviewStatusUpdate, ReviewCommentCreate, ReviewResponseCreate,
    ReviewDetail, ReviewSummary, ReviewTimeline, ReviewStatistics, ReviewComment, ReviewResponse
)
from app.services.review_service import ReviewService
from app.models.review import ReviewStatus, ReviewType
from typing import List, Optional

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/tasks/{task_id}/reviews", response_model=Review, status_code=status.HTTP_201_CREATED)
def create_review(task_id: int, review: ReviewCreate, db: Session = Depends(get_db)):
    """タスクのレビューを作成（要件・タスク・サブタスクすべてに対応）"""
    review_service = ReviewService(db)
    try:
        return review_service.create_review(task_id, review)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/tasks/{task_id}/reviews", response_model=List[ReviewSummary])
def get_task_reviews(task_id: int, db: Session = Depends(get_db)):
    """タスクのレビュー一覧を取得（要件・タスク・サブタスクすべてに対応）"""
    review_service = ReviewService(db)
    return review_service.get_reviews_by_task(task_id)


@router.get("/statistics", response_model=ReviewStatistics)
def get_review_statistics(
    task_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """レビュー統計情報を取得"""
    review_service = ReviewService(db)
    return review_service.get_review_statistics(task_id=task_id)


@router.get("/{review_id}", response_model=Review)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """レビュー詳細を取得"""
    review_service = ReviewService(db)
    review = review_service.get_review(review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


@router.get("/{review_id}/detail", response_model=ReviewDetail)
def get_review_detail(review_id: int, db: Session = Depends(get_db)):
    """レビューの詳細情報を取得（コメントとレスポンスを含む）"""
    review_service = ReviewService(db)
    review_detail = review_service.get_review_detail(review_id)
    if not review_detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review_detail


@router.put("/{review_id}", response_model=Review)
def update_review(review_id: int, review_update: ReviewUpdate, db: Session = Depends(get_db)):
    """レビューを更新"""
    review_service = ReviewService(db)
    updated_review = review_service.update_review(review_id, review_update)
    if not updated_review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return updated_review


@router.put("/{review_id}/status", response_model=Review)
def update_review_status(review_id: int, status_update: ReviewStatusUpdate, db: Session = Depends(get_db)):
    """レビューの状態を更新"""
    review_service = ReviewService(db)
    try:
        updated_review = review_service.update_review_status(review_id, status_update)
        if not updated_review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        return updated_review
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{review_id}/comments", response_model=ReviewComment, status_code=status.HTTP_201_CREATED)
def add_review_comment(review_id: int, comment: ReviewCommentCreate, db: Session = Depends(get_db)):
    """レビューコメントを追加"""
    review_service = ReviewService(db)
    try:
        return review_service.add_review_comment(review_id, comment)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{review_id}/comments", response_model=List[ReviewComment])
def get_review_comments(review_id: int, db: Session = Depends(get_db)):
    """レビューのコメント一覧を取得"""
    review_service = ReviewService(db)
    return review_service.get_review_comments(review_id)


@router.post("/{review_id}/responses", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def add_review_response(review_id: int, response: ReviewResponseCreate, db: Session = Depends(get_db)):
    """レビュー対応を追加"""
    review_service = ReviewService(db)
    try:
        return review_service.add_review_response(review_id, response)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{review_id}/responses", response_model=List[ReviewResponse])
def get_review_responses(review_id: int, db: Session = Depends(get_db)):
    """レビューの対応一覧を取得"""
    review_service = ReviewService(db)
    return review_service.get_review_responses(review_id)


@router.put("/{review_id}/responses/{response_id}/complete", response_model=ReviewResponse)
def complete_review_response(review_id: int, response_id: int, db: Session = Depends(get_db)):
    """レビュー対応を完了"""
    review_service = ReviewService(db)
    completed_response = review_service.complete_review_response(review_id, response_id)
    if not completed_response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review response not found")
    return completed_response


@router.get("/{review_id}/timeline", response_model=ReviewTimeline)
def get_review_timeline(review_id: int, db: Session = Depends(get_db)):
    """レビューのタイムライン情報を取得"""
    review_service = ReviewService(db)
    timeline = review_service.get_review_timeline(review_id)
    if not timeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return timeline


@router.get("/", response_model=List[ReviewSummary])
def search_reviews(
    status: Optional[ReviewStatus] = Query(None),
    review_type: Optional[ReviewType] = Query(None),
    reviewer: Optional[str] = Query(None),
    task_id: Optional[int] = Query(None),
    sort: str = Query("created_at"),
    order: str = Query("desc"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """レビューを検索"""
    review_service = ReviewService(db)
    return review_service.search_reviews(
        status=status, review_type=review_type, reviewer=reviewer, task_id=task_id,
        sort=sort, order=order, offset=offset, limit=limit
    )


# 階層レベル別のレビュー管理
@router.post("/requirements/{req_id}/reviews", response_model=Review, status_code=status.HTTP_201_CREATED)
def create_requirement_review(req_id: int, review: ReviewCreate, db: Session = Depends(get_db)):
    """要件のレビューを作成"""
    review_service = ReviewService(db)
    try:
        return review_service.create_review(req_id, review)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/requirements/{req_id}/reviews", response_model=List[ReviewSummary])
def get_requirement_reviews(req_id: int, db: Session = Depends(get_db)):
    """要件のレビュー一覧を取得"""
    review_service = ReviewService(db)
    return review_service.get_reviews_by_task(req_id)




@router.post("/subtasks/{subtask_id}/reviews", response_model=Review, status_code=status.HTTP_201_CREATED)
def create_subtask_review(subtask_id: int, review: ReviewCreate, db: Session = Depends(get_db)):
    """サブタスクのレビューを作成"""
    review_service = ReviewService(db)
    try:
        return review_service.create_review(subtask_id, review)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/subtasks/{subtask_id}/reviews", response_model=List[ReviewSummary])
def get_subtask_reviews(subtask_id: int, db: Session = Depends(get_db)):
    """サブタスクのレビュー一覧を取得"""
    review_service = ReviewService(db)
    return review_service.get_reviews_by_task(subtask_id)
