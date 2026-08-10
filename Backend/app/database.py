"""DB 연결 및 세션 관련 정의."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent  # Backend/
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "board.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 클론 직후에도 별도 준비 없이 바로 실행되도록 데이터 디렉터리를 미리 생성한다
DATA_DIR.mkdir(parents=True, exist_ok=True)

# check_same_thread=False : FastAPI가 여러 스레드에서 요청을 처리하므로 SQLite 제약을 완화한다
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection: object, connection_record: object) -> None:
    """SQLite는 기본적으로 외래키 제약을 강제하지 않으므로 연결마다 켜준다.

    댓글(comments.post_id)이 게시글 삭제 시 함께 삭제되도록(ON DELETE CASCADE)
    하려면 이 PRAGMA가 필요하다.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """모든 ORM 모델의 베이스 클래스."""


def get_db() -> Generator[Session, None, None]:
    """요청 단위 DB 세션을 제공하는 FastAPI 의존성."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
