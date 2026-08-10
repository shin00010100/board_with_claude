"""FastAPI 진입점."""

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import post

# 이 시점에는 app.routers.post -> app.services.post -> app.models.post로
# 이어지는 import 체인을 통해 Post 모델이 이미 Base.metadata에 등록되어 있다.
# 별도 마이그레이션 도구(Alembic 등) 없이 SQLite 파일에 테이블이 없으면 생성한다.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="게시판 API")

# CORS 미들웨어는 추가하지 않는다.
# 브라우저는 항상 Nginx(단일 origin)에만 접속하고, Nginx가 내부적으로
# /(프론트)와 /api/(백엔드)를 각각 프록시하므로 브라우저가 :8000에 직접
# 교차 출처 요청을 보낼 일이 없다.

app.include_router(post.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    """Nginx 앞단 없이 uvicorn 단독 기동 확인용 헬스체크."""
    return {"status": "ok"}
