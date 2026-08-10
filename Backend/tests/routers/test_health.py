"""헬스체크 엔드포인트로 FastAPI + TestClient 배선을 확인한다."""

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
