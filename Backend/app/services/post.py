"""게시글 비즈니스 로직 계층. repository를 호출하며 DB 쿼리를 직접 실행하지 않는다."""

from sqlalchemy.orm import Session

from app.models.post import Post
from app.repository import post as post_repository
from app.schemas.post import PostCreate, PostUpdate
from app.services.errors import InvalidPasswordError
from app.services.security import hash_password, verify_password

PAGE_SIZE = 10

__all__ = [
    "PAGE_SIZE",
    "PostNotFoundError",
    "InvalidPasswordError",
    "hash_password",
    "verify_password",
    "get_post_list",
    "get_post",
    "create_post",
    "update_post",
    "delete_post",
]


class PostNotFoundError(Exception):
    """게시글을 찾을 수 없을 때 발생한다."""


def get_post_list(db: Session, page: int) -> tuple[list[Post], int]:
    """게시글 목록을 10개씩 페이지 단위로 조회한다."""
    return post_repository.list_posts(db, page, PAGE_SIZE)


def get_post(db: Session, post_id: str) -> Post:
    """게시글 단건을 조회하고 조회수를 증가시킨다."""
    post = post_repository.get_post_by_id(db, post_id)
    if post is None:
        raise PostNotFoundError(post_id)
    post_repository.increment_view_count(db, post_id)
    post.view_count += 1
    return post


def create_post(db: Session, data: PostCreate) -> Post:
    """비밀번호를 해싱하여 게시글을 생성한다."""
    post = Post(
        title=data.title,
        content=data.content,
        author=data.author,
        password_hash=hash_password(data.password),
    )
    return post_repository.create_post(db, post)


def update_post(db: Session, post_id: str, data: PostUpdate) -> Post:
    """비밀번호 검증 후 게시글을 수정한다."""
    post = post_repository.get_post_by_id(db, post_id)
    if post is None:
        raise PostNotFoundError(post_id)
    if not verify_password(data.password, post.password_hash):
        raise InvalidPasswordError(post_id)

    updated = post_repository.update_post(
        db, post_id, title=data.title, content=data.content, author=data.author
    )
    if updated is None:
        raise PostNotFoundError(post_id)
    return updated


def delete_post(db: Session, post_id: str, password: str) -> None:
    """비밀번호 검증 후 게시글을 삭제한다."""
    post = post_repository.get_post_by_id(db, post_id)
    if post is None:
        raise PostNotFoundError(post_id)
    if not verify_password(password, post.password_hash):
        raise InvalidPasswordError(post_id)

    deleted = post_repository.delete_post(db, post_id)
    if not deleted:
        raise PostNotFoundError(post_id)
