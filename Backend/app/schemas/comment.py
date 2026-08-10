"""댓글 Pydantic 스키마 (요청/응답 검증)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    """댓글 작성 요청."""

    author: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1)
    password: str = Field(min_length=1)


class CommentDeleteRequest(BaseModel):
    """댓글 삭제 요청. 비밀번호는 로그에 남지 않도록 요청 바디로 전달한다."""

    password: str = Field(min_length=1)


class CommentResponse(BaseModel):
    """댓글 응답. 비밀번호(해시 포함) 필드는 노출하지 않는다."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    post_id: str
    author: str
    content: str
    created_at: datetime
