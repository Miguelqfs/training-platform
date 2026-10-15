import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app(storage="memory")) as test_client:
        yield test_client


def test_add_and_list_users_with_both_roles(client: TestClient) -> None:
    assert client.get("/users/").json() == []

    student = client.post(
        "/users/",
        json={
            "username": "maria",
            "password": "Abcdef12",
            "email": "maria@example.com",
        },
    )
    admin = client.post(
        "/users/",
        json={
            "username": "ana",
            "password": "Abcdef12",
            "email": "ana@example.com",
            "role": "admin",
        },
    )

    assert student.status_code == 201
    assert admin.status_code == 201
    expected_users = [
        {"id": 1, "username": "maria", "email": "maria@example.com", "role": "student"},
        {"id": 2, "username": "ana", "email": "ana@example.com", "role": "admin"},
    ]
    assert student.json() == expected_users[0]
    assert admin.json() == expected_users[1]
    assert client.get("/users/").json() == expected_users


def test_rejects_duplicate_username_or_email_without_case_sensitivity(
    client: TestClient,
) -> None:
    client.post(
        "/users/",
        json={
            "username": "Maria",
            "password": "Abcdef12",
            "email": "Maria@example.com",
        },
    )

    duplicate_username = client.post(
        "/users/",
        json={
            "username": " MARIA ",
            "password": "Abcdef12",
            "email": "other@example.com",
        },
    )
    duplicate_email = client.post(
        "/users/",
        json={
            "username": "other",
            "password": "Abcdef12",
            "email": "maria@EXAMPLE.com",
        },
    )

    assert duplicate_username.status_code == 409
    assert duplicate_email.status_code == 409
    assert len(client.get("/users/").json()) == 1


@pytest.mark.parametrize(
    "payload,field",
    [
        (
            {"username": "   ", "password": "Abcdef12", "email": "maria@example.com"},
            "username",
        ),
        (
            {"username": "maria", "password": "Abcdef12", "email": "not-an-email"},
            "email",
        ),
        (
            {
                "username": "maria",
                "password": "Abcdef12",
                "email": "maria@example.com",
                "role": "trainer",
            },
            "role",
        ),
    ],
)
def test_rejects_invalid_input(
    client: TestClient, payload: dict[str, str], field: str
) -> None:
    response = client.post("/users/", json=payload)
    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", field]
    assert error["type"]
    assert error["msg"]
    assert "input" not in error
    assert "ctx" not in error
    assert client.get("/users/").json() == []


def test_new_app_has_an_empty_collection(client: TestClient) -> None:
    client.post(
        "/users/",
        json={
            "username": "maria",
            "password": "Abcdef12",
            "email": "maria@example.com",
        },
    )

    with TestClient(create_app(storage="memory")) as another_client:
        assert another_client.get("/users/").json() == []
