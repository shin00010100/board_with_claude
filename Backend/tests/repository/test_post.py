"""repository/post.py 공개 함수 테스트. 실제 data/board.db가 아닌 테스트 DB를 사용한다."""

from sqlalchemy.orm import Session

from app.models.post import Post
from app.repository import post as post_repository


def _make_post(**overrides: str) -> Post:
    defaults: dict[str, str] = {
        "title": "제목",
        "content": "내용",
        "author": "작성자",
        "password_hash": "hashed-password",
    }
    defaults.update(overrides)
    return Post(**defaults)


def test_create_post_fills_server_managed_fields(db_session: Session) -> None:
    created = post_repository.create_post(db_session, _make_post())

    assert created.id
    assert created.title == "제목"
    assert created.view_count == 0
    assert created.created_at is not None
    assert created.updated_at is not None


def test_get_post_by_id_found_and_missing(db_session: Session) -> None:
    created = post_repository.create_post(db_session, _make_post())

    found = post_repository.get_post_by_id(db_session, created.id)
    assert found is not None
    assert found.id == created.id
    assert found.title == created.title

    assert post_repository.get_post_by_id(db_session, "존재하지-않는-id") is None


def test_list_posts_pagination_and_order(db_session: Session) -> None:
    for i in range(3):
        post_repository.create_post(db_session, _make_post(title=f"제목{i}"))

    page1, total = post_repository.list_posts(db_session, page=1, size=2)
    assert total == 3
    assert len(page1) == 2
    assert page1[0].created_at >= page1[1].created_at

    page2, total2 = post_repository.list_posts(db_session, page=2, size=2)
    assert total2 == 3
    assert len(page2) == 1


def test_update_post(db_session: Session) -> None:
    created = post_repository.create_post(db_session, _make_post())

    updated = post_repository.update_post(
        db_session, created.id, title="수정된 제목", content="수정된 내용", author="수정자"
    )
    assert updated is not None
    assert updated.title == "수정된 제목"
    assert updated.content == "수정된 내용"
    assert updated.author == "수정자"
    assert updated.updated_at >= created.updated_at

    missing = post_repository.update_post(
        db_session, "존재하지-않는-id", title="x", content="x", author="x"
    )
    assert missing is None


def test_delete_post(db_session: Session) -> None:
    created = post_repository.create_post(db_session, _make_post())

    assert post_repository.delete_post(db_session, created.id) is True
    assert post_repository.get_post_by_id(db_session, created.id) is None
    assert post_repository.delete_post(db_session, created.id) is False


def test_increment_view_count(db_session: Session) -> None:
    created = post_repository.create_post(db_session, _make_post())

    post_repository.increment_view_count(db_session, created.id)
    post_repository.increment_view_count(db_session, created.id)

    found = post_repository.get_post_by_id(db_session, created.id)
    assert found is not None
    assert found.view_count == 2
