import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import Mock, call

import pytest
from fastapi.testclient import TestClient

from app.accesses.domain import AccessEvent
from app.accesses.ports import AccessLogPort
from app.main import create_app
from app.users.domain import NewUser, PersistenceError, UserRole
from app.workouts.domain import WorkoutRegistration

NOW = datetime(2026, 11, 11, 12, tzinfo=UTC)
SECRET = "SenhaPrivada12"
EMAIL = "privado@example.com"
HASH = "hash-privado"
WORKOUT = {"user_id": 2, "name": SECRET, "description": EMAIL}
OPERATIONS = ("create", "get", "update", "delete")


@pytest.fixture
def access_log():
    return Mock(spec=AccessLogPort)


@pytest.fixture
def clock():
    return Mock(return_value=NOW.astimezone(timezone(timedelta(hours=-3))))


@pytest.fixture(params=["memory", "sqlite"])
def client(request, tmp_path, access_log, clock):
    app = create_app(
        storage=request.param,
        database_path=tmp_path / "accesses.db",
        access_log=access_log,
        clock=clock,
    )
    for username, email in (("outro", "outro@example.com"), ("dono", EMAIL)):
        app.state.context.repositories.users.add(
            NewUser(username, email, UserRole.STUDENT, HASH)
        )
    with TestClient(app) as client:
        yield client


def repositories(client):
    return client.app.state.context.repositories


def events(client):
    return repositories(client).accesses.list_between(
        NOW - timedelta(seconds=1), NOW + timedelta(seconds=1)
    )


def seed_workout(client):
    return repositories(client).workouts.add(WorkoutRegistration(**WORKOUT))


def perform(client, operation):
    if operation == "create":
        return client.post("/workouts/", json=WORKOUT)
    if operation == "get":
        return client.get("/workouts/1")
    if operation == "update":
        return client.put("/workouts/1", json={"name": "Novo"})
    return client.delete("/workouts/1")


def test_success_records_owner_and_utc_once_per_operation(client, access_log, clock):
    operations = ("create", "get", "get", "update", "delete")
    for operation, status in zip(operations, (201, 200, 200, 200, 204), strict=True):
        assert perform(client, operation).status_code == status
    expected = [AccessEvent(2, operation, NOW) for operation in operations]
    assert events(client) == expected
    assert access_log.record.call_args_list == [call(event) for event in expected]
    assert clock.call_count == len(expected)
    assert all(event.occurred_at.tzinfo is UTC for event in events(client))
    assert repositories(client).workouts.list_workouts() == []
    assert client.get("/statistics/entities").json() == {"total": 2}


@pytest.mark.parametrize(
    "method,url,body,status",
    [
        ("get", "/workouts/", None, 200),
        ("get", "/users/", None, 200),
        ("get", "/statistics/entities", None, 200),
        ("get", "/workouts/999", None, 404),
        ("put", "/workouts/999", {"name": "Novo"}, 404),
        ("delete", "/workouts/999", None, 404),
        ("post", "/workouts/", {**WORKOUT, "user_id": 999}, 404),
        ("get", "/workouts/0", None, 422),
        ("post", "/workouts/", {**WORKOUT, "password": SECRET}, 422),
        ("put", "/workouts/1", {"name": "", "password_hash": HASH}, 422),
    ],
)
def test_ineligible_requests_record_nothing(
    client, access_log, clock, method, url, body, status
):
    seed_workout(client)
    before = repositories(client).workouts.list_workouts()
    response = client.request(method, url, **({"json": body} if body else {}))
    assert response.status_code == status
    assert repositories(client).workouts.list_workouts() == before
    assert events(client) == []
    access_log.record.assert_not_called()
    clock.assert_not_called()


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize("stage", ("workout", "event", "commit"))
def test_failures_roll_back_workout_and_event_before_logging(
    client, access_log, monkeypatch, operation, stage
):
    seed_workout(client)
    # Preservar também eventos anteriores, inclusive quando a falha ocorre após escrita.
    repositories(client).accesses.add(AccessEvent(2, "create", NOW))
    repos = repositories(client)
    before_workouts, before_events = repos.workouts.list_workouts(), events(client)

    with monkeypatch.context() as patch:
        if stage == "commit":
            transaction = repos.unit_of_work.transaction

            @contextmanager
            def fail_commit():
                with transaction() as tx:
                    yield tx
                    raise PersistenceError("SQL/private/path " + SECRET)

            patch.setattr(repos.unit_of_work, "transaction", fail_commit)
        else:
            repository_type = type(
                repos.workouts if stage == "workout" else repos.accesses
            )
            method = (
                {
                    "create": "add",
                    "get": "get_by_id",
                    "update": "update",
                    "delete": "delete",
                }[operation]
                if stage == "workout"
                else "add"
            )
            original = getattr(repository_type, method)

            def fail_after_write(self, *args):
                original(self, *args)
                raise PersistenceError("SQL/private/path " + SECRET)

            patch.setattr(repository_type, method, fail_after_write)
        response = perform(client, operation)

    assert response.status_code == 503
    assert response.json() == {"detail": PersistenceError.WORKOUT_MESSAGE}
    assert repos.workouts.list_workouts() == before_workouts
    assert events(client) == before_events
    access_log.record.assert_not_called()
    assert (
        perform(client, operation).status_code
        == {"create": 201, "get": 200, "update": 200, "delete": 204}[operation]
    )
    assert events(client) == before_events + [AccessEvent(2, operation, NOW)]
    access_log.record.assert_called_once_with(AccessEvent(2, operation, NOW))
    if operation == "create":
        assert [workout.id for workout in repos.workouts.list_workouts()] == [1, 2]


@pytest.mark.parametrize("client", ["sqlite"], indirect=True)
@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize("failure", ["ABORT", "FAIL", "deferred"])
def test_sqlite_driver_and_commit_failures_are_atomic(
    client, tmp_path, access_log, operation, failure
):
    seed_workout(client)
    before = repositories(client).workouts.list_workouts()
    with sqlite3.connect(tmp_path / "accesses.db") as db:
        if failure == "deferred":
            db.execute(
                "CREATE TABLE pending (user_id INTEGER REFERENCES users(id) DEFERRABLE INITIALLY DEFERRED)"
            )
            trigger = "INSERT INTO pending VALUES (999);"
        else:
            trigger = f"SELECT RAISE({failure}, 'private database failure');"
        db.execute(
            f"CREATE TRIGGER fail_event AFTER INSERT ON access_events BEGIN {trigger} END"
        )
    response = perform(client, operation)
    assert response.status_code == 503
    assert response.json() == {"detail": PersistenceError.WORKOUT_MESSAGE}
    assert repositories(client).workouts.list_workouts() == before
    assert events(client) == []
    access_log.record.assert_not_called()
    with sqlite3.connect(tmp_path / "accesses.db") as db:
        db.execute("DROP TRIGGER fail_event")
    assert perform(client, operation).is_success
    assert events(client) == [AccessEvent(2, operation, NOW)]


@pytest.mark.parametrize("operation", OPERATIONS)
def test_auxiliary_log_failure_preserves_success_and_committed_event(
    client, access_log, operation, caplog
):
    seed_workout(client)
    observed_events = []

    def fail_after_commit(event):
        observed_events.append(events(client))
        raise RuntimeError(SECRET + EMAIL + HASH)

    access_log.record.side_effect = fail_after_commit
    response = perform(client, operation)
    assert (
        response.status_code
        == {"create": 201, "get": 200, "update": 200, "delete": 204}[operation]
    )
    assert events(client) == [AccessEvent(2, operation, NOW)]
    assert observed_events == [[AccessEvent(2, operation, NOW)]]
    access_log.record.assert_called_once_with(AccessEvent(2, operation, NOW))
    assert all(secret not in caplog.text for secret in (SECRET, EMAIL, HASH))


def test_real_adapter_logs_only_event_fields_in_real_flow(tmp_path, caplog):
    app = create_app(
        storage="sqlite", database_path=tmp_path / "log.db", clock=lambda: NOW
    )
    repos = app.state.context.repositories
    for username, email in (("outro", "outro@example.com"), ("dono", EMAIL)):
        repos.users.add(NewUser(username, email, UserRole.STUDENT, HASH))
    with (
        caplog.at_level(logging.INFO, logger="app.accesses"),
        TestClient(app) as client,
    ):
        for operation in OPERATIONS:
            assert perform(client, operation).is_success
        records = [record for record in caplog.records if record.name == "app.accesses"]
        assert [record.args for record in records] == [
            (2, operation, NOW.isoformat()) for operation in OPERATIONS
        ]
        assert all(
            record.msg == "user_id=%s operation=%s occurred_at=%s"
            and record.exc_info is None
            for record in records
        )
        for event in events(client):
            assert set(asdict(event)) == {"user_id", "operation", "occurred_at"}
        emitted = repr([record.__dict__ for record in records]) + repr(events(client))
        assert all(
            secret not in emitted
            for secret in (SECRET, EMAIL, HASH, "password", "description")
        )


@pytest.mark.parametrize("storage", ["memory", "sqlite"])
def test_real_recording_survives_restart_only_in_sqlite(storage, tmp_path):
    path = tmp_path / "restart.db"
    app = create_app(storage=storage, database_path=path, clock=lambda: NOW)
    repos = app.state.context.repositories
    user = repos.users.add(NewUser("dono", EMAIL, UserRole.STUDENT, HASH))
    with TestClient(app) as client:
        assert (
            client.post("/workouts/", json={**WORKOUT, "user_id": user.id}).status_code
            == 201
        )
    reopened = create_app(
        storage=storage, database_path=path
    ).state.context.repositories
    assert reopened.accesses.list_between(NOW, NOW + timedelta(seconds=1)) == (
        [AccessEvent(user.id, "create", NOW)] if storage == "sqlite" else []
    )
