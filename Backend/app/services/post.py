"""게시글 비즈니스 로직 계층. repository를 호출하며 DB 쿼리를 직접 실행하지 않는다."""

import hashlib
import hmac
import os

from sqlalchemy.orm import Session

from app.models.post import Post
from app.repository import post as post_repository
from app.schemas.post import PostCreate, PostUpdate

PAGE_SIZE = 10

_HASH_ALGORITHM = "sha256"
_HASH_ITERATIONS = 260_000


class PostNotFoundError(Exception):
    """게시글을 찾을 수 없을 때 발생한다."""


class InvalidPasswordError(Exception):
    """비밀번호가 일치하지 않을 때 발생한다."""


def hash_password(plain: str) -> str:
    """비밀번호를 랜덤 솔트와 함께 해싱한다. 저장 형식: '<salt_hex>$<hash_hex>'."""
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac(_HASH_ALGORITHM, plain.encode("utf-8"), salt, _HASH_ITERATIONS)
    return f"{salt.hex()}${derived.hex()}"


def verify_password(plain: str, password_hash: str) -> bool:
    """평문 비밀번호와 저장된 해시가 일치하는지 검증한다."""
    try:
        salt_hex, derived_hex = password_hash.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(derived_hex)
    candidate = hashlib.pbkdf2_hmac(_HASH_ALGORITHM, plain.encode("utf-8"), salt, _HASH_ITERATIONS)
    return hmac.compare_digest(candidate, expected)


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
