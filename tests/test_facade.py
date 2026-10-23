import subprocess
import sys
from dataclasses import FrozenInstanceError

import pytest
from fastapi.testclient import TestClient

from app.facade import FacadeSingletonController
from app.main import create_app
from app.users.domain import User, UserRole

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
