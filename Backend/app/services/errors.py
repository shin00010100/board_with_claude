"""서비스 계층 공통 예외."""


class InvalidPasswordError(Exception):
    """비밀번호가 일치하지 않을 때 발생한다."""
