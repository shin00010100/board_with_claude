"""services/comment.py 공개 함수 테스트."""

import pytest
from sqlalchemy.orm import Session

from app.models.post import Post
from app.repository import post as post_repository
from app.schemas.comment import CommentCreate
from app.services import comment as comment_service


def _make_post(db_session: Session) -> Post:
    return post_repository.create_post(
        db_session,
        Post(title="제목", content="내용", author="작성자", password_hash="hashed"),
    )


def test_create_comment_never_exposes_plain_password(db_session: Session) -> None:
    post = _make_post(db_session)

    created = comment_service.create_comment(
        db_session, post.id, CommentCreate(author="댓글러", content="내용", password="비밀-패스워드")
    )

    assert created.password_hash != "비밀-패스워드"


def test_create_comment_missing_post_raises(db_session: Session) -> None:
    with pytest.raises(comment_service.PostNotFoundError):
        comment_service.create_comment(
            db_session,
            "존재하지-않는-id",
            CommentCreate(author="댓글러", content="내용", password="pw"),
        )


def test_get_comments_missing_post_raises(db_session: Session) -> None:
    with pytest.raises(comment_service.PostNotFoundError):
        comment_service.get_comments(db_session, "존재하지-않는-id")


def test_get_comments_returns_created_comments(db_session: Session) -> None:
    post = _make_post(db_session)
    comment_service.create_comment(
        db_session, post.id, CommentCreate(author="댓글러", content="내용1", password="pw")
    )
    comment_service.create_comment(
        db_session, post.id, CommentCreate(author="댓글러2", content="내용2", password="pw")
    )

    comments = comment_service.get_comments(db_session, post.id)

    assert [c.content for c in comments] == ["내용1", "내용2"]


def test_delete_comment_requires_correct_password(db_session: Session) -> None:
    post = _make_post(db_session)
    created = comment_service.create_comment(
        db_session, post.id, CommentCreate(author="댓글러", content="내용", password="correct-pw")
    )

    with pytest.raises(comment_service.InvalidPasswordError):
        comment_service.delete_comment(db_session, post.id, created.id, "wrong-pw")

    comment_service.delete_comment(db_session, post.id, created.id, "correct-pw")
    assert comment_service.get_comments(db_session, post.id) == []


def test_delete_comment_missing_raises(db_session: Session) -> None:
    post = _make_post(db_session)
    with pytest.raises(comment_service.CommentNotFoundError):
        comment_service.delete_comment(db_session, post.id, "존재하지-않는-id", "아무-비밀번호")
