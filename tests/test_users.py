import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app()) as test_client:
        yield test_client


def test_add_and_list_users_with_both_roles(client: TestClient) -> None:
    assert client.get("/users/").json() == []

    student = client.post(
        "/users/", json={"username": "maria", "email": "maria@example.com"}
    )
    admin = client.post(
        "/users/",
        json={"username": "ana", "email": "ana@example.com", "role": "admin"},
    )

    assert student.status_code == 201
    assert admin.status_code == 201
    assert client.get("/users/").json() == [
        {"id": 1, "username": "maria", "email": "maria@example.com", "role": "student"},
        {"id": 2, "username": "ana", "email": "ana@example.com", "role": "admin"},
    ]


def test_rejects_duplicate_username_or_email_without_case_sensitivity(client: TestClient) -> None:
    client.post(
        "/users/", json={"username": "Maria", "email": "Maria@example.com"}
    )

    duplicate_username = client.post(
        "/users/", json={"username": " MARIA ", "email": "other@example.com"}
    )
    duplicate_email = client.post(
        "/users/", json={"username": "other", "email": "maria@EXAMPLE.com"}
    )

    assert duplicate_username.status_code == 409
    assert duplicate_email.status_code == 409
    assert len(client.get("/users/").json()) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "   ", "email": "maria@example.com"},
        {"username": "maria", "email": "not-an-email"},
        {"username": "maria", "email": "maria@example.com", "role": "trainer"},
    ],
)
def test_rejects_invalid_input(client: TestClient, payload: dict[str, str]) -> None:
    assert client.post("/users/", json=payload).status_code == 422
    assert client.get("/users/").json() == []


def test_new_app_has_an_empty_collection(client: TestClient) -> None:
    client.post(
        "/users/", json={"username": "maria", "email": "maria@example.com"}
    )

    with TestClient(create_app()) as another_client:
        assert another_client.get("/users/").json() == []
