import subprocess
import sys
from dataclasses import FrozenInstanceError

import pytest
from fastapi.testclient import TestClient

from app.facade import FacadeSingletonController
from app.main import create_app
from app.users.domain import User, UserRole
from app.workouts.domain import Workout

USER = {"username": "maria", "email": "maria@example.com", "password": "Abcdef12"}


def test_initial_concurrent_construction_in_fresh_process():
    script = """
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, local, settrace
import inspect
from app.facade import FacadeSingletonController
assert FacadeSingletonController._instance is None
barrier = Barrier(16)
lines, first_line = inspect.getsourcelines(FacadeSingletonController.__new__)
lock_line = first_line + next(i for i, line in enumerate(lines) if "with cls._lock:" in line)
state = local()
def trace(frame, event, arg):
    if (event == "line" and frame.f_code is FacadeSingletonController.__new__.__code__
        and frame.f_lineno == lock_line and not getattr(state, "arrived", False)):
        state.arrived = True
        barrier.wait(timeout=10)
    return trace
# Força todas as primeiras chamadas a passar pela checagem externa antes da trava.
settrace(trace)
def obtain(index):
    return (FacadeSingletonController() if index % 2 else FacadeSingletonController.get_instance())
with ThreadPoolExecutor(max_workers=16) as executor:
    instances = list(executor.map(obtain, range(16)))
assert len({id(instance) for instance in instances}) == 1
assert instances[0] is FacadeSingletonController.get_instance()
assert vars(instances[0]) == {}
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr


def test_singleton_identity_survives_app_creation_and_context_is_frozen():
    facade = FacadeSingletonController.get_instance()
    first = create_app(storage="memory")
    second = create_app(storage="memory")
    assert (
        facade
        is FacadeSingletonController()
        is FacadeSingletonController.get_instance()
    )
    assert first.state.context is not second.state.context
    with pytest.raises(FrozenInstanceError):
        first.state.context.users = second.state.context.users
    assert vars(facade) == {}


@pytest.mark.parametrize("storage", ["memory", "sqlite"])
def test_apps_are_independent_and_first_remains_functional(storage, tmp_path):
    first_app = create_app(storage=storage, database_path=tmp_path / "first.db")
    facade = FacadeSingletonController.get_instance()
    with TestClient(first_app) as first:
        first.post("/users/", json=USER)
        second_app = create_app(storage=storage, database_path=tmp_path / "second.db")
        with TestClient(second_app) as second:
            assert second.get("/users/").json() == []
            assert second.get("/workouts/").json() == []
            assert second.get("/statistics/entities").json() == {"total": 0}
            assert len(first.get("/users/").json()) == 1
            assert (
                first.post(
                    "/workouts/", json={"user_id": 1, "name": "Primeiro"}
                ).status_code
                == 201
            )
            assert (
                second.post(
                    "/workouts/", json={"user_id": 1, "name": "Inválido"}
                ).status_code
                == 404
            )
            assert first.get("/statistics/entities").json() == {"total": 2}
            assert facade.count_entities(first_app.state.context) == 2
            assert facade.count_entities(second_app.state.context) == 0
            assert type(facade.count_entities(first_app.state.context)) is int


def test_active_apps_share_only_their_configured_sqlite_file(tmp_path):
    database = tmp_path / "shared.db"
    first_app = create_app(storage="sqlite", database_path=database)
    original_context = first_app.state.context
    with TestClient(first_app) as first:
        first.post("/users/", json=USER)
        first.post("/workouts/", json={"user_id": 1, "name": "Compartilhado"})
        second_app = create_app(storage="sqlite", database_path=database)
        with TestClient(second_app) as second:
            assert second_app.state.context is not original_context
            assert second.get("/users/").json() == first.get("/users/").json()
            assert second.get("/workouts/").json() == first.get("/workouts/").json()
            assert (
                second.put(
                    "/workouts/1",
                    json={"name": "Modificado", "description": "Pela segunda"},
                ).status_code
                == 200
            )
            assert first.get("/workouts/1").json() == dict(
                id=1, user_id=1, name="Modificado", description="Pela segunda"
            )
            assert first_app.state.context is original_context
            assert (
                first.get("/statistics/entities").json()
                == second.get("/statistics/entities").json()
                == {"total": 2}
            )


def test_explicit_config_overrides_environment_for_both_repositories(
    monkeypatch, tmp_path
):
    ignored = tmp_path / "ignored.db"
    selected = tmp_path / "selected.db"
    monkeypatch.setenv("USER_STORAGE", "unknown")
    monkeypatch.setenv("USER_DATABASE", str(ignored))
    with TestClient(create_app(storage="sqlite", database_path=selected)) as client:
        assert client.post("/users/", json=USER).status_code == 201
        assert (
            client.post("/workouts/", json={"user_id": 1, "name": "Plano"}).status_code
            == 201
        )
    assert selected.exists()
    assert not ignored.exists()
    with TestClient(create_app(storage="sqlite", database_path=selected)) as client:
        assert client.get("/statistics/entities").json() == {"total": 2}
    with TestClient(create_app(storage="memory")) as client:
        assert client.get("/statistics/entities").json() == {"total": 0}


def test_environment_selects_both_repositories(monkeypatch, tmp_path):
    monkeypatch.setenv("USER_STORAGE", "sqlite")
    monkeypatch.setenv("USER_DATABASE", str(tmp_path / "environment.db"))
    with TestClient(create_app()) as client:
        client.post("/users/", json=USER)
        assert (
            client.post("/workouts/", json={"user_id": 1, "name": "Plano"}).status_code
            == 201
        )
    with TestClient(create_app()) as client:
        assert client.get("/statistics/entities").json() == {"total": 2}
        assert client.get("/workouts/").json() == [
            dict(id=1, user_id=1, name="Plano", description="")
        ]


@pytest.mark.parametrize(
    "case",
    [
        (
            "post",
            "/users/",
            USER,
            "register_user",
            User(42, "maria", "maria@example.com", UserRole.STUDENT, "private-hash"),
            201,
        ),
        (
            "get",
            "/users/",
            None,
            "list_users",
            [User(42, "maria", "maria@example.com", UserRole.STUDENT, "private-hash")],
            200,
        ),
        (
            "post",
            "/workouts/",
            {"user_id": 7, "name": "Novo"},
            "create_workout",
            Workout(42, 7, "Dublê", "Texto"),
            201,
        ),
        (
            "get",
            "/workouts/42",
            None,
            "get_workout",
            Workout(42, 7, "Dublê", "Texto"),
            200,
        ),
        (
            "get",
            "/workouts/",
            None,
            "list_workouts",
            [Workout(42, 7, "Dublê", "Texto")],
            200,
        ),
        (
            "put",
            "/workouts/42",
            {"name": "Novo"},
            "update_workout",
            Workout(42, 7, "Dublê", "Texto"),
            200,
        ),
        ("delete", "/workouts/42", None, "delete_workout", None, 204),
        ("get", "/statistics/entities", None, "count_entities", 7, 200),
    ],
)
def test_every_route_uses_facade_with_its_own_context(monkeypatch, case):
    method, url, body, operation, result, status = case
    app = create_app(storage="memory")
    calls = []

    def substitute(self, context, *args):
        calls.append((self, context, args))
        return result

    monkeypatch.setattr(FacadeSingletonController, operation, substitute)
    with TestClient(app) as client:
        response = client.request(method, url, **({"json": body} if body else {}))
        assert response.status_code == status
        if operation == "count_entities":
            assert response.json() == {"total": 7}
        elif status == 204:
            assert response.content == b""
        else:
            value = response.json()
            assert (value[0] if isinstance(value, list) else value)["id"] == 42
        assert "private-hash" not in response.text
    assert len(calls) == 1
    assert calls[0][0] is FacadeSingletonController.get_instance()
    assert calls[0][1] is app.state.context
    arguments = calls[0][2]
    if operation in ("get_workout", "update_workout", "delete_workout"):
        assert arguments[0] == 42
    if operation == "register_user":
        assert arguments[0].username == "maria"
    if operation == "create_workout":
        assert arguments[0].user_id == 7 and arguments[0].name == "Novo"
    if operation == "update_workout":
        assert arguments[1].name == "Novo"
    assert app.state.context.users.list_users() == []
    assert app.state.context.workouts.list_workouts() == []
