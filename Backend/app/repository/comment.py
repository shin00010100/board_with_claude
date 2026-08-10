"""댓글 repository 계층.

posts/repository/post.py와 동일한 규칙을 따른다: 모든 DB 접근은 이 계층에서만
수행하고, 각 함수는 raw SQL(text())과 SQLAlchemy ORM 두 방식을 1:1로 병기한다.
기본은 SQL 활성 / ORM 주석 처리이며, 각 블록은 자체 return까지 포함해 독립적으로
완결되어 있어 서로 바꿔 활성화해도 동일하게 동작한다.
"""

import uuid
from typing import Any, Mapping

from sqlalchemy import DateTime, String, Text, text
from sqlalchemy.orm import Session

from app.models.comment import Comment

_COMMENT_COLUMN_TYPES: dict[str, Any] = dict(
    id=String,
    post_id=String,
    author=String,
    content=Text,
    password_hash=String,
    created_at=DateTime,
)

_SELECT_COLUMNS = "id, post_id, author, content, password_hash, created_at"


def _row_to_comment(row: Mapping[str, Any]) -> Comment:
    """raw SQL 조회 결과(Mapping)를 Comment 객체로 변환한다."""
    return Comment(
        id=row["id"],
        post_id=row["post_id"],
        author=row["author"],
        content=row["content"],
        password_hash=row["password_hash"],
        created_at=row["created_at"],
    )


def list_comments_by_post(db: Session, post_id: str) -> list[Comment]:
    """특정 게시글의 댓글을 오래된 순으로 전부 조회한다."""
    # --- SQL 방식 (기본 활성) ---
    stmt = text(
        f"SELECT {_SELECT_COLUMNS} FROM comments WHERE post_id = :post_id ORDER BY created_at ASC"
    ).columns(**_COMMENT_COLUMN_TYPES)
    rows = db.execute(stmt, {"post_id": post_id}).mappings().all()
    return [_row_to_comment(row) for row in rows]
    # --- ORM 방식 (주석 처리, 참고용) ---
    # return (
    #     db.query(Comment)
    #     .filter(Comment.post_id == post_id)
    #     .order_by(Comment.created_at.asc())
    #     .all()
    # )


def get_comment_by_id(db: Session, comment_id: str) -> Comment | None:
    """ID로 댓글 단건을 조회한다."""
    # --- SQL 방식 (기본 활성) ---
    stmt = text(f"SELECT {_SELECT_COLUMNS} FROM comments WHERE id = :id").columns(
        **_COMMENT_COLUMN_TYPES
    )
    row = db.execute(stmt, {"id": comment_id}).mappings().first()
    return _row_to_comment(row) if row is not None else None
    # --- ORM 방식 (주석 처리, 참고용) ---
    # return db.query(Comment).filter(Comment.id == comment_id).first()


def create_comment(db: Session, comment: Comment) -> Comment:
    """댓글을 생성한다. id가 비어 있으면 여기서 채운다."""
    comment_id = comment.id or str(uuid.uuid4())

    # --- SQL 방식 (기본 활성) ---
    stmt = text(
        "INSERT INTO comments (id, post_id, author, content, password_hash) "
        "VALUES (:id, :post_id, :author, :content, :password_hash) "
        f"RETURNING {_SELECT_COLUMNS}"
    ).columns(**_COMMENT_COLUMN_TYPES)
    row = (
        db.execute(
            stmt,
            {
                "id": comment_id,
                "post_id": comment.post_id,
                "author": comment.author,
                "content": comment.content,
                "password_hash": comment.password_hash,
            },
        )
        .mappings()
        .one()
    )
    db.commit()
    return _row_to_comment(row)
    # --- ORM 방식 (주석 처리, 참고용) ---
    # comment.id = comment_id
    # db.add(comment)
    # db.commit()
    # db.refresh(comment)
    # return comment


def delete_comment(db: Session, comment_id: str) -> bool:
    """댓글을 삭제한다. 비밀번호 검증은 service 계층에서 선행한다."""
    # --- SQL 방식 (기본 활성) ---
    result = db.execute(text("DELETE FROM comments WHERE id = :id"), {"id": comment_id})
    db.commit()
    return result.rowcount > 0
    # --- ORM 방식 (주석 처리, 참고용) ---
    # comment = db.query(Comment).filter(Comment.id == comment_id).first()
    # if comment is None:
    #     return False
    # db.delete(comment)
    # db.commit()
    # return True
