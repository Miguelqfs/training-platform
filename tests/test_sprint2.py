import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.users.domain import (
    DuplicateUserError,
    InvalidLoginError,
    InvalidPasswordError,
    NewUser,
    PersistenceError,
    UserRegistration,
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


@pytest.mark.parametrize(
    "username,message",
    [
        ("", "Login não pode ser vazio"),
        ("   ", "Login não pode ser vazio"),
        ("a" * 13, "Login deve ter no máximo 12 caracteres"),
        ("user1", "Login não pode conter números"),
        ("user١", "Login não pode conter números"),
        ("user²", "Login não pode conter números"),
    ],
)
def test_invalid_login_does_not_save(username: str, message: str) -> None:
    service = UserService(MemoryUserRepository())
    with pytest.raises(InvalidLoginError, match=message):
        service.add_user(
            UserRegistration(
                username=username,
                email="maria@example.com",
                role=UserRole.STUDENT,
                password="Abcdef12",
            )
        )
    assert service.list_users() == []


@pytest.mark.parametrize(
    "password,message",
    [
        ("", "Senha deve ter de 8 a 128 caracteres"),
        ("Abc1234", "Senha deve ter de 8 a 128 caracteres"),
        ("Aa1" + "a" * 126, "Senha deve ter de 8 a 128 caracteres"),
        ("abcdefgh", "Senha deve conter pelo menos 3 categorias"),
        ("ABCDEFG1", "Senha deve conter pelo menos 3 categorias"),
        ("Abcdefgh", "Senha deve conter pelo menos 3 categorias"),
        ("abcdefg?", "Senha deve conter pelo menos 3 categorias"),
        ("Abcdefg?", "Senha deve conter pelo menos 3 categorias"),
    ],
)
def test_invalid_password_does_not_save(password: str, message: str) -> None:
    with TestClient(create_app(storage="memory")) as client:
        response = client.post("/users/", json=payload(password=password))
        assert response.status_code == 422
        assert response.json()["detail"].startswith(message)
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
        UserRegistration(
            username=" Maria ",
            email="MARIA@example.com",
            role=UserRole.STUDENT,
            password="Abcdef12",
        )
    )
    algorithm, iterations, salt, digest = user.password_hash.split("$")
    assert algorithm == "pbkdf2_sha256"
    assert int(iterations) == 600_000
    assert len(bytes.fromhex(salt)) == 16
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
            service.add_user(
                UserRegistration(
                    username=username,
                    email=email,
                    role=UserRole.ADMIN,
                    password="Abcdef12",
                )
            )
    assert len(service.list_users()) == 1


def test_sqlite_survives_restart_and_continues_ids(tmp_path: Path) -> None:
    database = tmp_path / "users.db"
    with TestClient(create_app(storage="sqlite", database_path=database)) as client:
        response = client.post("/users/", json=payload())
        assert response.status_code == 201
        saved_user = response.json()
    with TestClient(create_app(storage="sqlite", database_path=database)) as client:
        assert client.get("/users/").json() == [saved_user]
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
            repository.add(
                NewUser(
                    username="maria",
                    email="maria@example.com",
                    role=UserRole.STUDENT,
                    password_hash="hash",
                )
            )
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
        ("Abcdefg!", "a@example.com", "aBCDEFG!"),
        ("maria", "abcdef1!@example.com", "abcdef1!@example.com"),
        ("other", "abc123@example.com", "ABC123@EXAMPLE.COM"),
    ],
)
def test_password_cannot_equal_normalized_identity(
    username: str, email: str, password: str
) -> None:
    service = UserService(MemoryUserRepository())
    with pytest.raises(
        InvalidPasswordError, match="Senha não pode ser igual ao login ou e-mail"
    ):
        service.add_user(
            UserRegistration(
                username=username,
                email=email,
                role=UserRole.STUDENT,
                password=password,
            )
        )
    assert service.list_users() == []


def test_numeric_login_error_identifies_the_rule() -> None:
    with TestClient(create_app(storage="memory")) as client:
        response = client.post("/users/", json=payload("user١"))
        assert response.status_code == 422
        assert response.json() == {"detail": "Login não pode conter números"}
        assert client.get("/users/").json() == []


@pytest.mark.parametrize("storage", ["memory", "sqlite"])
def test_same_password_uses_distinct_salts(storage: str, tmp_path: Path) -> None:
    repository = (
        MemoryUserRepository()
        if storage == "memory"
        else SQLiteUserRepository(tmp_path / "users.db")
    )
    service = UserService(repository)
    users = [
        service.add_user(
            UserRegistration(
                username=username,
                email=f"{username}@example.com",
                role=UserRole.STUDENT,
                password="Abcdef12",
            )
        )
        for username in ("maria", "ana")
    ]
    assert users[0].password_hash.split("$")[2] != users[1].password_hash.split("$")[2]


def test_sqlite_write_failure_leaves_no_partial_user(tmp_path: Path) -> None:
    database = tmp_path / "users.db"
    with TestClient(create_app(storage="sqlite", database_path=database)) as client:
        assert client.post("/users/", json=payload()).status_code == 201
        with sqlite3.connect(database) as connection:
            connection.execute("""CREATE TRIGGER fail_insert AFTER INSERT ON users
                BEGIN SELECT RAISE(ABORT, 'simulated write failure'); END""")
        response = client.post("/users/", json=payload("ana"))
        assert response.status_code == 503
        assert [user["username"] for user in client.get("/users/").json()] == ["maria"]
        with sqlite3.connect(database) as connection:
            assert connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
            connection.execute("DROP TRIGGER fail_insert")
        response = client.post("/users/", json=payload("ana"))
        assert response.status_code == 201
        assert response.json()["id"] == 2
