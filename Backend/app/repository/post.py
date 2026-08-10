"""게시글 repository 계층.

모든 DB 접근(쿼리 실행)은 이 계층에서만 수행한다.
각 함수는 raw SQL(text())과 SQLAlchemy ORM 두 가지 방식을 1:1로 병기한다.
기본 상태는 SQL 활성 / ORM 주석 처리이며, 어느 한쪽만 실행해도 동일한
결과를 반환하도록 각 블록을 독립적으로 완결된 형태(자체 return 포함)로 작성한다.
"""

import uuid
from typing import Any, Mapping

from sqlalchemy import DateTime, Integer, String, Text, text
from sqlalchemy.orm import Session

from app.models.post import Post

# raw SQL 조회 결과에 타입을 명시해, sqlite에 문자열로 저장된 datetime 값이
# 파이썬 datetime 객체로 자동 변환되도록 한다 (ORM 경로와 동일한 타입 보장).
_POST_COLUMN_TYPES: dict[str, Any] = dict(
    id=String,
    title=String,
    content=Text,
    author=String,
    password_hash=String,
    view_count=Integer,
    created_at=DateTime,
    updated_at=DateTime,
)

_SELECT_COLUMNS = "id, title, content, author, password_hash, view_count, created_at, updated_at"


def _row_to_post(row: Mapping[str, Any]) -> Post:
    """raw SQL 조회 결과(Mapping)를 Post 객체로 변환한다."""
    return Post(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        author=row["author"],
        password_hash=row["password_hash"],
        view_count=row["view_count"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def list_posts(db: Session, page: int, size: int) -> tuple[list[Post], int]:
    """게시글 목록을 페이지 단위로 조회하고 전체 개수를 함께 반환한다."""
    offset = (page - 1) * size

    # --- SQL 방식 (기본 활성) ---
    stmt = text(
        f"SELECT {_SELECT_COLUMNS} FROM posts ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
    ).columns(**_POST_COLUMN_TYPES)
    rows = db.execute(stmt, {"limit": size, "offset": offset}).mappings().all()
    posts = [_row_to_post(row) for row in rows]
    total = db.execute(text("SELECT COUNT(*) FROM posts")).scalar_one()
    return posts, total
    # --- ORM 방식 (주석 처리, 참고용) ---
    # posts = (
    #     db.query(Post)
    #     .order_by(Post.created_at.desc())
    #     .limit(size)
    #     .offset(offset)
    #     .all()
    # )
    # total = db.query(Post).count()
    # return posts, total


def get_post_by_id(db: Session, post_id: str) -> Post | None:
    """ID로 게시글 단건을 조회한다."""
    # --- SQL 방식 (기본 활성) ---
    stmt = text(f"SELECT {_SELECT_COLUMNS} FROM posts WHERE id = :id").columns(**_POST_COLUMN_TYPES)
    row = db.execute(stmt, {"id": post_id}).mappings().first()
    return _row_to_post(row) if row is not None else None
    # --- ORM 방식 (주석 처리, 참고용) ---
    # return db.query(Post).filter(Post.id == post_id).first()


def create_post(db: Session, post: Post) -> Post:
    """게시글을 생성한다.

    id/view_count는 서버가 채우는 값이므로, 호출 측이 비워 둔 경우(단순
    `Post(title=..., ...)` 생성 시 컬럼 기본값은 ORM flush 시점에만 적용되어
    이 시점엔 비어 있을 수 있음) 여기서 기본값을 직접 채운다.
    """
    post_id = post.id or str(uuid.uuid4())
    view_count = post.view_count if post.view_count is not None else 0

    # --- SQL 방식 (기본 활성) ---
    stmt = text(
        "INSERT INTO posts (id, title, content, author, password_hash, view_count) "
        "VALUES (:id, :title, :content, :author, :password_hash, :view_count) "
        f"RETURNING {_SELECT_COLUMNS}"
    ).columns(**_POST_COLUMN_TYPES)
    row = (
        db.execute(
            stmt,
            {
                "id": post_id,
                "title": post.title,
                "content": post.content,
                "author": post.author,
                "password_hash": post.password_hash,
                "view_count": view_count,
            },
        )
        .mappings()
        .one()
    )
    db.commit()
    return _row_to_post(row)
    # --- ORM 방식 (주석 처리, 참고용) ---
    # post.id = post_id
    # post.view_count = view_count
    # db.add(post)
    # db.commit()
    # db.refresh(post)
    # return post


def update_post(db: Session, post_id: str, title: str, content: str, author: str) -> Post | None:
    """게시글을 수정한다. 비밀번호 검증은 service 계층에서 선행한다."""
    # --- SQL 방식 (기본 활성) ---
    # updated_at은 ORM의 onupdate=func.now()가 raw SQL 경로에는 적용되지
    # 않으므로 여기서 직접 CURRENT_TIMESTAMP로 갱신한다.
    stmt = text(
        "UPDATE posts SET title = :title, content = :content, author = :author, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = :id "
        f"RETURNING {_SELECT_COLUMNS}"
    ).columns(**_POST_COLUMN_TYPES)
    row = (
        db.execute(stmt, {"title": title, "content": content, "author": author, "id": post_id})
        .mappings()
        .first()
    )
    db.commit()
    return _row_to_post(row) if row is not None else None
    # --- ORM 방식 (주석 처리, 참고용) ---
    # post = db.query(Post).filter(Post.id == post_id).first()
    # if post is None:
    #     return None
    # post.title = title
    # post.content = content
    # post.author = author
    # db.commit()
    # db.refresh(post)
    # return post


def delete_post(db: Session, post_id: str) -> bool:
    """게시글을 삭제한다. 비밀번호 검증은 service 계층에서 선행한다."""
    # --- SQL 방식 (기본 활성) ---
    result = db.execute(text("DELETE FROM posts WHERE id = :id"), {"id": post_id})
    db.commit()
    return result.rowcount > 0
    # --- ORM 방식 (주석 처리, 참고용) ---
    # post = db.query(Post).filter(Post.id == post_id).first()
    # if post is None:
    #     return False
    # db.delete(post)
    # db.commit()
    # return True


def increment_view_count(db: Session, post_id: str) -> None:
    """게시글 조회수를 1 증가시킨다."""
    # --- SQL 방식 (기본 활성) ---
    db.execute(text("UPDATE posts SET view_count = view_count + 1 WHERE id = :id"), {"id": post_id})
    db.commit()
    return
    # --- ORM 방식 (주석 처리, 참고용) ---
    # post = db.query(Post).filter(Post.id == post_id).first()
    # if post is not None:
    #     post.view_count += 1
    #     db.commit()
