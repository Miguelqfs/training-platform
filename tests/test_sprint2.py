import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.users.domain import (
    DuplicateUserError,
    InvalidCredentialsError,
    PersistenceError,
    UserRole,
)
from app.users.repository import MemoryUserRepository, SQLiteUserRepository
from app.users.service import UserService


def payload(username: str = "maria", password: str = "Abcdef12") -> dict[str, str]:
    return {
        "username": username,
        "email": f"{username}@example.com",
        "password": password,
    }


@pytest.mark.parametrize("username", ["", "   ", "a" * 13, "user1", "user١", "user²"])
def test_invalid_login_does_not_save(username: str) -> None:
    service = UserService()
    with pytest.raises(InvalidCredentialsError):
        service.add_user(username, "maria@example.com", UserRole.STUDENT, "Abcdef12")
    assert service.list_users() == []


@pytest.mark.parametrize(
    "password",
    [
        "",
        "Abc1234",
        "Aa1" + "a" * 126,
        "abcdefgh",
        "ABCDEFG1",
        "Abcdefgh",
        "abcdefg?",
        "Abcdefg?",
    ],
)
def test_invalid_password_does_not_save(password: str) -> None:
    with TestClient(create_app(storage="memory")) as client:
        assert (
            client.post("/users/", json=payload(password=password)).status_code == 422
        )
        assert client.get("/users/").json() == []


@pytest.mark.parametrize(
    "password", ["Abcdef12", "Abcdefg!", "ABCDEF1!", "abcdef1!", "Aa1" + "a" * 125]
)
def test_iam_accepts_three_categories_and_length_boundaries(password: str) -> None:
    with TestClient(create_app(storage="memory")) as client:
        assert (
            client.post("/users/", json=payload("a" * 12, password)).status_code == 201
        )
        assert "password" not in client.get("/users/").text


@pytest.mark.parametrize("storage", ["memory", "sqlite"])
def test_repository_uniqueness_and_password_hash(storage: str, tmp_path: Path) -> None:
    repository = (
        MemoryUserRepository()
        if storage == "memory"
        else SQLiteUserRepository(tmp_path / "users.db")
    )
    service = UserService(repository)
    user = service.add_user(
        " Maria ", "MARIA@example.com", UserRole.STUDENT, "Abcdef12"
    )
    algorithm, iterations, salt, digest = user.password_hash.split("$")
    assert algorithm == "pbkdf2_sha256"
    assert (
        hashlib.pbkdf2_hmac(
            "sha256", b"Abcdef12", bytes.fromhex(salt), int(iterations)
        ).hex()
        == digest
    )
    assert "password_hash" not in repr(user)
    for username, email in [
        ("MARIA", "other@example.com"),
        ("other", "Maria@example.com"),
    ]:
        with pytest.raises(DuplicateUserError):
            service.add_user(username, email, UserRole.ADMIN, "Abcdef12")
    assert len(service.list_users()) == 1


def test_sqlite_survives_restart_and_continues_ids(tmp_path: Path) -> None:
    database = tmp_path / "users.db"
    with TestClient(create_app(storage="sqlite", database_path=database)) as client:
        assert client.post("/users/", json=payload()).status_code == 201
    with TestClient(create_app(storage="sqlite", database_path=database)) as client:
        assert client.get("/users/").json()[0]["username"] == "maria"
        assert client.post("/users/", json=payload()).status_code == 409
        assert client.post("/users/", json=payload("ana")).json()["id"] == 2
    assert b"Abcdef12" not in database.read_bytes()


def test_storage_failures_are_handled_without_exposing_database(tmp_path: Path) -> None:
    database = tmp_path / "users.db"
    app = create_app(storage="sqlite", database_path=database)
    with sqlite3.connect(database) as connection:
        connection.execute("DROP TABLE users")
    with TestClient(app) as client:
        for response in (client.get("/users/"), client.post("/users/", json=payload())):
            assert response.status_code == 503
            assert response.json() == {
                "detail": "Armazenamento de usuários indisponível"
            }
    with pytest.raises(PersistenceError):
        create_app(storage="sqlite", database_path=tmp_path / "missing" / "users.db")
    database.write_bytes(b"invalid database")
    with pytest.raises(PersistenceError):
        create_app(storage="sqlite", database_path=database)


def test_storage_selection_from_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("USER_STORAGE", "sqlite")
    monkeypatch.setenv("USER_DATABASE", str(tmp_path / "users.db"))
    with TestClient(create_app()) as client:
        assert client.post("/users/", json=payload()).status_code == 201
    with TestClient(create_app()) as client:
        assert len(client.get("/users/").json()) == 1
    monkeypatch.setenv("USER_STORAGE", "unknown")
    with pytest.raises(ValueError):
        create_app()


@pytest.mark.parametrize("storage", ["memory", "sqlite"])
def test_concurrent_duplicates_save_once(storage: str, tmp_path: Path) -> None:
    repository = (
        MemoryUserRepository()
        if storage == "memory"
        else SQLiteUserRepository(tmp_path / "users.db")
    )

    def add() -> bool:
        try:
            repository.add("maria", "maria@example.com", UserRole.STUDENT, "hash")
            return True
        except DuplicateUserError:
            return False

    with ThreadPoolExecutor(max_workers=4) as executor:
        assert sum(executor.map(lambda _: add(), range(4))) == 1
    assert len(repository.list_users()) == 1


def test_invalid_request_never_echoes_password() -> None:
    with TestClient(create_app(storage="memory")) as client:
        data = payload()
        data["email"] = "invalid"
        response = client.post("/users/", json=data)
        assert response.status_code == 422
        assert "Abcdef12" not in response.text
        data["password"] = {"secret": "Abcdef12"}
        response = client.post("/users/", json=data)
        assert response.status_code == 422
        assert "Abcdef12" not in response.text


@pytest.mark.parametrize(
    "username,email,password",
    [
        ("Abcdefg!", "a@example.com", "Abcdefg!"),
        ("maria", "abcdef1!@example.com", "abcdef1!@example.com"),
    ],
)
def test_password_cannot_equal_normalized_identity(
    username: str, email: str, password: str
) -> None:
    service = UserService()
    with pytest.raises(InvalidCredentialsError):
        service.add_user(username, email, UserRole.STUDENT, password)
    assert service.list_users() == []
