"""댓글 비즈니스 로직 계층. repository를 호출하며 DB 쿼리를 직접 실행하지 않는다."""

from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.repository import comment as comment_repository
from app.repository import post as post_repository
from app.schemas.comment import CommentCreate
from app.services.errors import InvalidPasswordError
from app.services.post import PostNotFoundError
from app.services.security import hash_password, verify_password

__all__ = [
    "PostNotFoundError",
    "CommentNotFoundError",
    "InvalidPasswordError",
    "get_comments",
    "create_comment",
    "delete_comment",
]


class CommentNotFoundError(Exception):
    """댓글을 찾을 수 없을 때 발생한다."""


def get_comments(db: Session, post_id: str) -> list[Comment]:
    """게시글의 댓글 목록을 조회한다. 게시글이 없으면 예외를 발생시킨다."""
    if post_repository.get_post_by_id(db, post_id) is None:
        raise PostNotFoundError(post_id)
    return comment_repository.list_comments_by_post(db, post_id)


def create_comment(db: Session, post_id: str, data: CommentCreate) -> Comment:
    """게시글에 비밀번호를 해싱해 댓글을 생성한다."""
    if post_repository.get_post_by_id(db, post_id) is None:
        raise PostNotFoundError(post_id)

    comment = Comment(
        post_id=post_id,
        author=data.author,
        content=data.content,
        password_hash=hash_password(data.password),
    )
    return comment_repository.create_comment(db, comment)


def delete_comment(db: Session, post_id: str, comment_id: str, password: str) -> None:
    """비밀번호 검증 후 댓글을 삭제한다."""
    comment = comment_repository.get_comment_by_id(db, comment_id)
    if comment is None or comment.post_id != post_id:
        raise CommentNotFoundError(comment_id)
    if not verify_password(password, comment.password_hash):
        raise InvalidPasswordError(comment_id)

    deleted = comment_repository.delete_comment(db, comment_id)
    if not deleted:
        raise CommentNotFoundError(comment_id)
