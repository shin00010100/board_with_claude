"""댓글 SQLAlchemy ORM 모델."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Comment(Base):
    """게시글에 달리는 댓글 테이블."""

    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # ondelete="CASCADE" + database.py의 PRAGMA foreign_keys=ON 조합으로
    # 게시글이 삭제되면 딸린 댓글도 DB 레벨에서 함께 삭제된다.
    post_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 게시글과 동일하게 삭제 시 비밀번호 검증을 위해 필요. 평문 저장 금지.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
