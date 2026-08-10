"""routers/comment.py 공개 엔드포인트 테스트 (HTTP 계층)."""

from fastapi.testclient import TestClient

_POSTS = "/api/posts"


def _create_post(client: TestClient, **overrides: str) -> dict:
    payload = {"title": "제목", "content": "내용", "author": "작성자", "password": "pw1234"}
    payload.update(overrides)
    response = client.post(_POSTS, json=payload)
    assert response.status_code == 201
    return response.json()


def _create_comment(client: TestClient, post_id: str, **overrides: str) -> dict:
    payload = {"author": "댓글러", "content": "댓글 내용", "password": "cpw1234"}
    payload.update(overrides)
    response = client.post(f"{_POSTS}/{post_id}/comments", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_and_list_comments(client: TestClient) -> None:
    post = _create_post(client)

    created = _create_comment(client, post["id"])
    assert created["post_id"] == post["id"]
    assert "password" not in created
    assert "password_hash" not in created

    response = client.get(f"{_POSTS}/{post['id']}/comments")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == created["id"]


def test_create_comment_on_missing_post_returns_404(client: TestClient) -> None:
    response = client.post(
        f"{_POSTS}/존재하지-않는-id/comments",
        json={"author": "댓글러", "content": "내용", "password": "pw"},
    )
    assert response.status_code == 404


def test_list_comments_on_missing_post_returns_404(client: TestClient) -> None:
    response = client.get(f"{_POSTS}/존재하지-않는-id/comments")
    assert response.status_code == 404


def test_create_comment_validation_error(client: TestClient) -> None:
    post = _create_post(client)
    response = client.post(
        f"{_POSTS}/{post['id']}/comments",
        json={"author": "", "content": "내용", "password": "pw"},
    )
    assert response.status_code == 422


def test_delete_comment_wrong_password(client: TestClient) -> None:
    post = _create_post(client)
    comment = _create_comment(client, post["id"], password="correct-pw")

    response = client.request(
        "DELETE",
        f"{_POSTS}/{post['id']}/comments/{comment['id']}",
        json={"password": "wrong-pw"},
    )
    assert response.status_code == 403


def test_delete_comment_success(client: TestClient) -> None:
    post = _create_post(client)
    comment = _create_comment(client, post["id"], password="correct-pw")

    response = client.request(
        "DELETE",
        f"{_POSTS}/{post['id']}/comments/{comment['id']}",
        json={"password": "correct-pw"},
    )
    assert response.status_code == 204

    remaining = client.get(f"{_POSTS}/{post['id']}/comments").json()
    assert remaining == []


def test_deleting_post_removes_its_comments(client: TestClient) -> None:
    post = _create_post(client, password="post-pw")
    _create_comment(client, post["id"])

    response = client.request("DELETE", f"{_POSTS}/{post['id']}", json={"password": "post-pw"})
    assert response.status_code == 204

    assert client.get(f"{_POSTS}/{post['id']}/comments").status_code == 404
