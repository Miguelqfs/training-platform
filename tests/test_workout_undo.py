import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

from app.accesses.domain import AccessEvent
from app.main import create_app
from app.users.domain import NewUser, PersistenceError, UserRole
from app.users.repository import SQLiteUserRepository
from app.workouts.domain import WorkoutRegistration
from app.workouts.repository import SQLiteWorkoutRepository

NOW = datetime(2026, 11, 25, tzinfo=UTC)


@pytest.fixture(params=("memory", "sqlite"))
def storage(request):
    return request.param


@pytest.fixture
def client(storage, tmp_path):
    app = create_app(
        storage=storage, database_path=tmp_path / "undo.db", clock=lambda: NOW
    )
    repos = app.state.context.repositories
    repos.users.add(NewUser("owner", "owner@example.com", UserRole.STUDENT, "hash"))
    with TestClient(app) as client:
        yield client


def test_undo_restores_only_the_last_successful_update(client):
    repos = client.app.state.context.repositories
    first = repos.workouts.add(WorkoutRegistration(1, "Peito", "Supino"))
    second = repos.workouts.add(WorkoutRegistration(1, "Pernas", "Agachamento"))
    url = f"/workouts/{first.id}"
    undo_url = f"{url}/undo"
    no_history = client.post(undo_url)
    assert no_history.status_code == 409
    assert no_history.json() == {
        "detail": "Nenhuma atualização disponível para desfazer"
    }

    previous = {"name": "Costas", "description": "Remada"}
    current = {"name": "Ombros", "description": "Elevação"}
    assert client.put(url, json=previous).status_code == 200
    assert client.put(url, json=current).status_code == 200
    assert client.put(url, json={"name": ""}).status_code == 422
    assert client.put(f"/workouts/{second.id}", json=current).status_code == 200

    restored = client.post(undo_url)
    assert restored.status_code == 200
    assert restored.json() == {**asdict(first), **previous}
    assert client.post(undo_url).status_code == 409
    assert asdict(repos.workouts.get_by_id(second.id)) == {**asdict(second), **current}
    assert client.post(f"/workouts/{second.id}/undo").json() == asdict(second)

    assert client.put(url, json=previous).status_code == 200
    assert client.post(undo_url).json() == restored.json()
    assert client.put(url, json=current).status_code == 200
    assert client.delete(url).status_code == 204
    assert client.post(undo_url).status_code == 404
    assert repos.mementos.get(first.id) is None
    assert client.post("/workouts/999/undo").status_code == 404
    assert client.post("/workouts/0/undo").status_code == 422

    events = repos.accesses.list_between(NOW, NOW + timedelta(seconds=1))
    assert [event.operation for event in events] == [
        "update",
        "update",
        "update",
        "undo",
        "undo",
        "update",
        "undo",
        "update",
        "delete",
    ]
    assert all(
        event.user_id == first.user_id and event.occurred_at == NOW for event in events
    )


def test_concurrent_undo_consumes_the_history_once(client, storage, tmp_path):
    repos = client.app.state.context.repositories
    workout = repos.workouts.add(WorkoutRegistration(1, "Peito", "Supino"))
    url = f"/workouts/{workout.id}"
    assert client.put(url, json={"name": "Costas"}).status_code == 200
    app = (
        create_app(
            storage="sqlite", database_path=tmp_path / "undo.db", clock=lambda: NOW
        )
        if storage == "sqlite"
        else client.app
    )
    barrier = Barrier(2, timeout=5)

    def undo(test_client):
        barrier.wait()
        return test_client.post(f"{url}/undo").status_code

    with TestClient(app) as other, ThreadPoolExecutor(max_workers=2) as workers:
        first = workers.submit(undo, client)
        second = workers.submit(undo, other)
        assert sorted((first.result(), second.result())) == [200, 409]
    assert repos.workouts.get_by_id(workout.id) == workout
    assert [
        event.operation
        for event in repos.accesses.list_between(NOW, NOW + timedelta(seconds=1))
    ] == ["update", "undo"]


def test_openapi_documents_undo_contract(client):
    paths = client.get("/openapi.json").json()["paths"]
    undo = paths["/workouts/{workout_id}/undo"]["post"]
    assert "requestBody" not in undo
    assert set(undo["responses"]) == {"200", "404", "409", "422", "503"}


@pytest.mark.parametrize("storage", ["sqlite"], indirect=True)
def test_sqlite_ignored_workout_write_preserves_workout_history_and_events(
    client, tmp_path
):
    repos = client.app.state.context.repositories
    workout = repos.workouts.add(WorkoutRegistration(1, "Peito", "Supino"))
    url = f"/workouts/{workout.id}"
    assert client.put(url, json={"name": "Costas"}).status_code == 200
    current = repos.workouts.get_by_id(workout.id)
    expected_events = [AccessEvent(workout.user_id, "update", NOW)]
    with closing(sqlite3.connect(tmp_path / "undo.db")) as db:
        db.execute(
            "CREATE TRIGGER ignore_workout_update BEFORE UPDATE ON workouts "
            "BEGIN SELECT RAISE(IGNORE); END"
        )

        for method, endpoint, payload in (
            ("PUT", url, {"name": "Pernas"}),
            ("POST", f"{url}/undo", None),
        ):
            response = client.request(method, endpoint, json=payload)
            assert response.status_code == 503
            assert response.json() == {"detail": PersistenceError.WORKOUT_MESSAGE}
            assert repos.workouts.get_by_id(workout.id) == current
            assert repos.mementos.get(workout.id) == workout.create_memento()
            assert (
                repos.accesses.list_between(NOW, NOW + timedelta(seconds=1))
                == expected_events
            )

        db.execute("DROP TRIGGER ignore_workout_update")

    assert client.post(f"{url}/undo").json() == asdict(workout)


def test_sqlite_migrates_legacy_events_and_can_undo_after_restart(tmp_path):
    path = tmp_path / "legacy.db"
    users = SQLiteUserRepository(path)
    user = users.add(NewUser("owner", "owner@example.com", UserRole.STUDENT, "hash"))
    workouts = SQLiteWorkoutRepository(path)
    workout = workouts.add(WorkoutRegistration(user.id, "Peito", "Supino"))
    occurred_at = NOW.isoformat(timespec="microseconds")
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("""CREATE TABLE access_events (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            operation TEXT NOT NULL CHECK (operation IN ('create', 'get', 'update', 'delete')),
            occurred_at TEXT NOT NULL
        )""")
        db.execute(
            "CREATE INDEX access_events_occurred_at ON access_events(occurred_at)"
        )
        db.execute(
            "INSERT INTO access_events VALUES (42, ?, 'create', ?)",
            (user.id, occurred_at),
        )

    url = f"/workouts/{workout.id}"
    with TestClient(
        create_app(storage="sqlite", database_path=path, clock=lambda: NOW)
    ) as client:
        assert client.post(f"{url}/undo").status_code == 409
        assert client.put(url, json={"name": "Costas"}).status_code == 200

    reopened = create_app(storage="sqlite", database_path=path, clock=lambda: NOW)
    with TestClient(reopened) as client:
        restored = client.post(f"{url}/undo")
        assert restored.status_code == 200
        assert restored.json() == asdict(workout)

    accesses = reopened.state.context.repositories.accesses
    assert accesses.list_between(NOW, NOW + timedelta(seconds=1)) == [
        AccessEvent(user.id, operation, NOW)
        for operation in ("create", "update", "undo")
    ]
    with closing(sqlite3.connect(path)) as db:
        assert db.execute("SELECT * FROM access_events WHERE id = 42").fetchone() == (
            42,
            user.id,
            "create",
            occurred_at,
        )
        assert (
            db.execute("PRAGMA index_info(access_events_occurred_at)").fetchone()[2]
            == "occurred_at"
        )
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
