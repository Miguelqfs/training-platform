import sqlite3
from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.accesses.domain import AccessEvent
from app.main import create_app
from app.users.domain import NewUser, PersistenceError, UserRole
from app.workouts.domain import WorkoutRegistration, WorkoutUpdate


@pytest.fixture(params=["memory", "sqlite"])
def configured(request, tmp_path):
    path = tmp_path / "app.db"
    app = create_app(storage=request.param, database_path=path)
    repos = app.state.context.repositories
    user = repos.users.add(
        NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash")
    )
    return request.param, path, repos, user


def test_event_interval_and_factory_isolation(configured):
    storage, path, repos, user = configured
    start = datetime(2026, 11, 11, tzinfo=UTC)
    events = [
        AccessEvent(user.id, "create", start),
        AccessEvent(user.id, "get", start + timedelta(hours=1)),
        AccessEvent(user.id, "delete", start + timedelta(hours=2)),
    ]
    for event in events:
        repos.accesses.add(event)
    assert repos.accesses.list_between(start, start + timedelta(hours=2)) == events[:2]
    assert (
        repos.accesses.list_between(
            start + timedelta(days=1), start + timedelta(days=2)
        )
        == []
    )
    reopened = create_app(
        storage=storage, database_path=path
    ).state.context.repositories
    assert reopened.accesses.list_between(start, start + timedelta(days=1)) == (
        events if storage == "sqlite" else []
    )
    assert len(reopened.users.list_users()) == (1 if storage == "sqlite" else 0)


def test_utc_normalization_and_invalid_intervals(configured):
    _, _, repos, user = configured
    start = datetime(2026, 1, 1, tzinfo=UTC)
    local = start.astimezone(timezone(timedelta(hours=-3)))
    repos.accesses.add(AccessEvent(user.id, "get", local))
    assert (
        repos.accesses.list_between(start, start + timedelta(seconds=1))[0].occurred_at
        == start
    )
    with pytest.raises(ValueError):
        repos.accesses.list_between(start, start)
    with pytest.raises(ValueError):
        repos.accesses.list_between(start.replace(tzinfo=None), start)


@pytest.mark.parametrize("action", ["create", "update", "delete"])
def test_workout_and_event_roll_back_together(configured, action):
    _, _, repos, user = configured
    workout = repos.workouts.add(WorkoutRegistration(user.id, "original", ""))
    event = AccessEvent(user.id, "create", datetime.now(UTC))
    with pytest.raises(RuntimeError):
        with repos.unit_of_work.transaction() as tx:
            if action == "create":
                tx.workouts.add(WorkoutRegistration(user.id, "new", ""))
            elif action == "update":
                tx.workouts.update(workout.id, WorkoutUpdate("changed", ""))
            else:
                tx.workouts.delete(workout.id)
            tx.accesses.add(event)
            raise RuntimeError("falha depois da gravação")
    assert repos.workouts.list_workouts() == [workout]
    assert (
        repos.accesses.list_between(
            event.occurred_at - timedelta(seconds=1),
            event.occurred_at + timedelta(seconds=1),
        )
        == []
    )


def test_transaction_commits_both(configured):
    _, _, repos, user = configured
    now = datetime.now(UTC)
    with repos.unit_of_work.transaction() as tx:
        workout = tx.workouts.add(WorkoutRegistration(user.id, "new", ""))
        tx.accesses.add(AccessEvent(user.id, "create", now))
    assert repos.workouts.get_by_id(workout.id) == workout
    assert (
        len(
            repos.accesses.list_between(
                now - timedelta(seconds=1), now + timedelta(seconds=1)
            )
        )
        == 1
    )


def test_sqlite_existing_database_is_preserved(tmp_path):
    path = tmp_path / "legacy.db"
    initial = create_app(
        storage="sqlite", database_path=path
    ).state.context.repositories
    user = initial.users.add(
        NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash")
    )
    workout = initial.workouts.add(WorkoutRegistration(user.id, "legado", ""))
    with sqlite3.connect(path) as db:
        db.execute("DROP TABLE access_events")
    repos = create_app(storage="sqlite", database_path=path).state.context.repositories
    assert repos.users.get_by_id(user.id) == user
    assert repos.workouts.get_by_id(workout.id) == workout
    assert (
        repos.accesses.list_between(
            datetime(2026, 1, 1, tzinfo=UTC), datetime(2027, 1, 1, tzinfo=UTC)
        )
        == []
    )


def test_sqlite_event_failure_reverts_workout(tmp_path):
    path = tmp_path / "app.db"
    repos = create_app(storage="sqlite", database_path=path).state.context.repositories
    user = repos.users.add(
        NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash")
    )
    with sqlite3.connect(path) as db:
        db.execute("DROP TABLE access_events")
    with pytest.raises(PersistenceError):
        with repos.unit_of_work.transaction() as tx:
            tx.workouts.add(WorkoutRegistration(user.id, "new", ""))
            tx.accesses.add(AccessEvent(user.id, "create", datetime.now(UTC)))
    assert repos.workouts.list_workouts() == []


def test_distinct_sqlite_files_are_isolated(tmp_path):
    first = create_app(
        storage="sqlite", database_path=tmp_path / "first.db"
    ).state.context.repositories
    second = create_app(
        storage="sqlite", database_path=tmp_path / "second.db"
    ).state.context.repositories
    user = first.users.add(
        NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash")
    )
    now = datetime.now(UTC)
    first.accesses.add(AccessEvent(user.id, "get", now))
    assert second.users.list_users() == []
    assert (
        second.accesses.list_between(
            now - timedelta(seconds=1), now + timedelta(seconds=1)
        )
        == []
    )


@pytest.mark.parametrize(
    "user_id,operation,occurred_at",
    [
        (0, "get", datetime(2026, 1, 1, tzinfo=UTC)),
        (True, "get", datetime(2026, 1, 1, tzinfo=UTC)),
        (1, "unknown", datetime(2026, 1, 1, tzinfo=UTC)),
        (1, "get", datetime(2026, 1, 1)),
    ],
)
def test_event_rejects_invalid_domain_data(user_id, operation, occurred_at):
    with pytest.raises(ValueError):
        AccessEvent(user_id, operation, occurred_at)


def test_event_normalizes_timezone_at_construction():
    local = datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=-3)))
    assert AccessEvent(1, "get", local).occurred_at == datetime(
        2026, 1, 1, 3, tzinfo=UTC
    )
