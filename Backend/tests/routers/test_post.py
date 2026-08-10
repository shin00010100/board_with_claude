"""routers/post.py 공개 엔드포인트 테스트 (HTTP 계층). 경로는 main.py의 /api 프리픽스 포함."""

from fastapi.testclient import TestClient

_BASE = "/api/posts"


def _create_post(client: TestClient, **overrides: str) -> dict:
    payload = {"title": "제목", "content": "내용", "author": "작성자", "password": "pw1234"}
    payload.update(overrides)
    response = client.post(_BASE, json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_and_get_post(client: TestClient) -> None:
    created = _create_post(client)
    assert created["view_count"] == 0
    assert "password" not in created
    assert "password_hash" not in created

    response = client.get(f"{_BASE}/{created['id']}")
    assert response.status_code == 200
    assert response.json()["view_count"] == 1


def test_get_post_not_found(client: TestClient) -> None:
    response = client.get(f"{_BASE}/존재하지-않는-id")
    assert response.status_code == 404


def test_create_post_validation_error(client: TestClient) -> None:
    response = client.post(
        _BASE, json={"title": "", "content": "내용", "author": "작성자", "password": "pw"}
    )
    assert response.status_code == 422


def test_list_posts_pagination(client: TestClient) -> None:
    for i in range(12):
        _create_post(client, title=f"제목{i}")

    response = client.get(_BASE, params={"page": 1})
    body = response.json()
    assert response.status_code == 200
    assert body["total"] == 12
    assert len(body["items"]) == 10
    assert body["size"] == 10

    response_page2 = client.get(_BASE, params={"page": 2})
    assert len(response_page2.json()["items"]) == 2


def test_update_post_wrong_password(client: TestClient) -> None:
    created = _create_post(client, password="correct-pw")

    response = client.put(
        f"{_BASE}/{created['id']}",
        json={"title": "수정", "content": "수정내용", "author": "수정자", "password": "wrong-pw"},
    )
    assert response.status_code == 403


def test_update_post_success(client: TestClient) -> None:
    created = _create_post(client, password="correct-pw")

    response = client.put(
        f"{_BASE}/{created['id']}",
        json={"title": "수정", "content": "수정내용", "author": "수정자", "password": "correct-pw"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "수정"


def test_delete_post_wrong_password(client: TestClient) -> None:
    created = _create_post(client, password="correct-pw")

    response = client.request("DELETE", f"{_BASE}/{created['id']}", json={"password": "wrong-pw"})
    assert response.status_code == 403


def test_delete_post_success(client: TestClient) -> None:
    created = _create_post(client, password="correct-pw")

    response = client.request("DELETE", f"{_BASE}/{created['id']}", json={"password": "correct-pw"})
    assert response.status_code == 204

    assert client.get(f"{_BASE}/{created['id']}").status_code == 404
