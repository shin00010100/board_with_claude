"""services/post.py 공개 함수 테스트."""

import pytest
from sqlalchemy.orm import Session

from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate
from app.services import post as post_service


def test_hash_and_verify_password_roundtrip() -> None:
    hashed = post_service.hash_password("비밀번호123")
    assert post_service.verify_password("비밀번호123", hashed) is True
    assert post_service.verify_password("틀린비밀번호", hashed) is False


def test_hash_password_uses_random_salt() -> None:
    first = post_service.hash_password("동일비밀번호")
    second = post_service.hash_password("동일비밀번호")
    assert first != second


def _create(db_session: Session, **overrides: str) -> Post:
    defaults: dict[str, str] = {
        "title": "제목",
        "content": "내용",
        "author": "작성자",
        "password": "pw1234",
    }
    defaults.update(overrides)
    return post_service.create_post(db_session, PostCreate(**defaults))


def test_create_post_never_exposes_plain_password(db_session: Session) -> None:
    created = _create(db_session, password="비밀-패스워드")
    assert created.password_hash != "비밀-패스워드"
    assert post_service.verify_password("비밀-패스워드", created.password_hash) is True


def test_get_post_increments_view_count(db_session: Session) -> None:
    created = _create(db_session)
    assert created.view_count == 0

    fetched = post_service.get_post(db_session, created.id)
    assert fetched.view_count == 1


def test_get_post_missing_raises(db_session: Session) -> None:
    with pytest.raises(post_service.PostNotFoundError):
        post_service.get_post(db_session, "존재하지-않는-id")


def test_get_post_list_paginates_by_page_size(db_session: Session) -> None:
    for i in range(12):
        _create(db_session, title=f"제목{i}")

    posts, total = post_service.get_post_list(db_session, page=1)
    assert total == 12
    assert len(posts) == post_service.PAGE_SIZE == 10

    posts_page2, _ = post_service.get_post_list(db_session, page=2)
    assert len(posts_page2) == 2


def test_update_post_requires_correct_password(db_session: Session) -> None:
    created = _create(db_session, password="correct-pw")

    with pytest.raises(post_service.InvalidPasswordError):
        post_service.update_post(
            db_session,
            created.id,
            PostUpdate(title="수정", content="수정내용", author="수정자", password="wrong-pw"),
        )

    updated = post_service.update_post(
        db_session,
        created.id,
        PostUpdate(title="수정", content="수정내용", author="수정자", password="correct-pw"),
    )
    assert updated.title == "수정"


def test_update_post_missing_raises(db_session: Session) -> None:
    with pytest.raises(post_service.PostNotFoundError):
        post_service.update_post(
            db_session,
            "존재하지-않는-id",
            PostUpdate(title="x", content="x", author="x", password="x"),
        )


def test_delete_post_requires_correct_password(db_session: Session) -> None:
    created = _create(db_session, password="correct-pw")

    with pytest.raises(post_service.InvalidPasswordError):
        post_service.delete_post(db_session, created.id, "wrong-pw")

    post_service.delete_post(db_session, created.id, "correct-pw")
    with pytest.raises(post_service.PostNotFoundError):
        post_service.get_post(db_session, created.id)


def test_delete_post_missing_raises(db_session: Session) -> None:
    with pytest.raises(post_service.PostNotFoundError):
        post_service.delete_post(db_session, "존재하지-않는-id", "아무-비밀번호")
