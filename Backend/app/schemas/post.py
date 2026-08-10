"""게시글 Pydantic 스키마 (요청/응답 검증)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostCreate(BaseModel):
    """게시글 작성 요청."""

    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)


class PostUpdate(BaseModel):
    """게시글 수정 요청. 비밀번호 일치 확인 후에만 수정 가능."""

    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)


class PostDeleteRequest(BaseModel):
    """게시글 삭제 요청. 비밀번호는 로그에 남지 않도록 요청 바디로 전달한다."""

    password: str = Field(min_length=1)


class PostResponse(BaseModel):
    """게시글 응답. 비밀번호(해시 포함) 필드는 노출하지 않는다."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: str
    author: str
    view_count: int
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    """게시글 목록 응답 (10개씩 페이지네이션)."""

    items: list[PostResponse]
    total: int
    page: int
    size: int
