"""댓글 API 엔드포인트. /api/posts/{post_id}/comments 경로에 마운트된다."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.comment import CommentCreate, CommentDeleteRequest, CommentResponse
from app.services import comment as comment_service

router = APIRouter(prefix="/posts", tags=["댓글"])

_POST_NOT_FOUND_DETAIL = "게시글을 찾을 수 없습니다"
_COMMENT_NOT_FOUND_DETAIL = "댓글을 찾을 수 없습니다"
_WRONG_PASSWORD_DETAIL = "비밀번호가 일치하지 않습니다"


@router.get("/{post_id}/comments", response_model=list[CommentResponse])
def list_comments(post_id: str, db: Session = Depends(get_db)) -> list[CommentResponse]:
    """게시글의 댓글 목록 조회."""
    try:
        comments = comment_service.get_comments(db, post_id)
    except comment_service.PostNotFoundError:
        raise HTTPException(status_code=404, detail=_POST_NOT_FOUND_DETAIL) from None
    return [CommentResponse.model_validate(c) for c in comments]


@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    post_id: str, data: CommentCreate, db: Session = Depends(get_db)
) -> CommentResponse:
    """댓글 작성 (비밀번호 필수)."""
    try:
        comment = comment_service.create_comment(db, post_id, data)
    except comment_service.PostNotFoundError:
        raise HTTPException(status_code=404, detail=_POST_NOT_FOUND_DETAIL) from None
    return CommentResponse.model_validate(comment)


@router.delete("/{post_id}/comments/{comment_id}", status_code=204)
def delete_comment(
    post_id: str, comment_id: str, data: CommentDeleteRequest, db: Session = Depends(get_db)
) -> None:
    """댓글 삭제 (비밀번호 일치 필요)."""
    try:
        comment_service.delete_comment(db, post_id, comment_id, data.password)
    except comment_service.CommentNotFoundError:
        raise HTTPException(status_code=404, detail=_COMMENT_NOT_FOUND_DETAIL) from None
    except comment_service.InvalidPasswordError:
        raise HTTPException(status_code=403, detail=_WRONG_PASSWORD_DETAIL) from None
