"""pytest 공용 설정. 실제 data/board.db가 아닌 인메모리 SQLite를 사용한다."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# StaticPool: 인메모리 SQLite는 커넥션마다 별도 DB가 생성되므로,
# 테스트 중 여러 커넥션이 동일한 DB를 공유하도록 고정한다.
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """테스트용 DB 세션. 테스트마다 스키마를 생성/삭제한다."""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """get_db 의존성을 테스트 세션으로 오버라이드한 TestClient."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
