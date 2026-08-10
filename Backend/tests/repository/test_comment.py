"""repository/comment.py 공개 함수 테스트. 실제 data/board.db가 아닌 테스트 DB를 사용한다."""

from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.post import Post
from app.repository import comment as comment_repository
from app.repository import post as post_repository


def _make_post(db_session: Session) -> Post:
    return post_repository.create_post(
        db_session,
        Post(title="제목", content="내용", author="작성자", password_hash="hashed"),
    )


def _make_comment(post_id: str, **overrides: str) -> Comment:
    defaults: dict[str, str] = {
        "post_id": post_id,
        "author": "댓글작성자",
        "content": "댓글 내용",
        "password_hash": "hashed-password",
    }
    defaults.update(overrides)
    return Comment(**defaults)


def test_create_comment_fills_server_managed_fields(db_session: Session) -> None:
    post = _make_post(db_session)

    created = comment_repository.create_comment(db_session, _make_comment(post.id))

    assert created.id
    assert created.post_id == post.id
    assert created.created_at is not None


def test_get_comment_by_id_found_and_missing(db_session: Session) -> None:
    post = _make_post(db_session)
    created = comment_repository.create_comment(db_session, _make_comment(post.id))

    found = comment_repository.get_comment_by_id(db_session, created.id)
    assert found is not None
    assert found.content == "댓글 내용"

    assert comment_repository.get_comment_by_id(db_session, "존재하지-않는-id") is None


def test_list_comments_by_post_ordered_oldest_first(db_session: Session) -> None:
    post = _make_post(db_session)
    other_post = _make_post(db_session)

    first = comment_repository.create_comment(db_session, _make_comment(post.id, content="첫번째"))
    second = comment_repository.create_comment(db_session, _make_comment(post.id, content="두번째"))
    comment_repository.create_comment(db_session, _make_comment(other_post.id, content="다른글 댓글"))

    comments = comment_repository.list_comments_by_post(db_session, post.id)

    assert [c.id for c in comments] == [first.id, second.id]


def test_delete_comment(db_session: Session) -> None:
    post = _make_post(db_session)
    created = comment_repository.create_comment(db_session, _make_comment(post.id))

    assert comment_repository.delete_comment(db_session, created.id) is True
    assert comment_repository.get_comment_by_id(db_session, created.id) is None
    assert comment_repository.delete_comment(db_session, created.id) is False


def test_deleting_post_cascades_to_its_comments(db_session: Session) -> None:
    """게시글 삭제 시 SQLite FK(ON DELETE CASCADE)로 댓글도 함께 삭제되는지 확인한다."""
    post = _make_post(db_session)
    comment = comment_repository.create_comment(db_session, _make_comment(post.id))

    assert post_repository.delete_post(db_session, post.id) is True

    assert comment_repository.get_comment_by_id(db_session, comment.id) is None
