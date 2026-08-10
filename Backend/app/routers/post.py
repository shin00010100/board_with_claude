"""게시글 API 엔드포인트."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.post import (
    PostCreate,
    PostDeleteRequest,
    PostListResponse,
    PostResponse,
    PostUpdate,
)
from app.services import post as post_service

router = APIRouter(prefix="/posts", tags=["게시글"])

_NOT_FOUND_DETAIL = "게시글을 찾을 수 없습니다"
_WRONG_PASSWORD_DETAIL = "비밀번호가 일치하지 않습니다"


@router.get("", response_model=PostListResponse)
def list_posts(page: int = Query(default=1, ge=1), db: Session = Depends(get_db)) -> PostListResponse:
    """게시판 목록 조회 (10개씩 페이지네이션)."""
    posts, total = post_service.get_post_list(db, page)
    return PostListResponse(
        items=[PostResponse.model_validate(post) for post in posts],
        total=total,
        page=page,
        size=post_service.PAGE_SIZE,
    )


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: str, db: Session = Depends(get_db)) -> PostResponse:
    """특정 게시물 조회 (조회수 1 증가)."""
    try:
        post = post_service.get_post(db, post_id)
    except post_service.PostNotFoundError:
        raise HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL) from None
    return PostResponse.model_validate(post)


@router.post("", response_model=PostResponse, status_code=201)
def create_post(data: PostCreate, db: Session = Depends(get_db)) -> PostResponse:
    """게시글 작성 (비밀번호 필수)."""
    post = post_service.create_post(db, data)
    return PostResponse.model_validate(post)


@router.put("/{post_id}", response_model=PostResponse)
def update_post(post_id: str, data: PostUpdate, db: Session = Depends(get_db)) -> PostResponse:
    """게시글 수정 (비밀번호 일치 필요)."""
    try:
        post = post_service.update_post(db, post_id, data)
    except post_service.PostNotFoundError:
        raise HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL) from None
    except post_service.InvalidPasswordError:
        raise HTTPException(status_code=403, detail=_WRONG_PASSWORD_DETAIL) from None
    return PostResponse.model_validate(post)


@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: str, data: PostDeleteRequest, db: Session = Depends(get_db)) -> None:
    """게시글 삭제 (비밀번호 일치 필요)."""
    try:
        post_service.delete_post(db, post_id, data.password)
    except post_service.PostNotFoundError:
        raise HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL) from None
    except post_service.InvalidPasswordError:
        raise HTTPException(status_code=403, detail=_WRONG_PASSWORD_DETAIL) from None
