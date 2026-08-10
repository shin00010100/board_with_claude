"""비밀번호 해싱/검증 유틸리티. post/comment 서비스가 공통으로 사용한다."""

import hashlib
import hmac
import os

_HASH_ALGORITHM = "sha256"
_HASH_ITERATIONS = 260_000


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
