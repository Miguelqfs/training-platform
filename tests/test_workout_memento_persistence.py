import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from threading import Barrier

import pytest

from app.accesses.domain import AccessEvent
from app.main import create_app
from app.users.domain import NewUser, PersistenceError, UserRole
from app.workouts.domain import (
    InvalidWorkoutError,
    Workout,
    WorkoutMemento,
    WorkoutNotFoundError,
    WorkoutRegistration,
    WorkoutUpdate,
)
from app.workouts.repository import SQLiteWorkoutMementoRepository


@pytest.fixture(params=["memory", "sqlite"])
def configured(request, tmp_path):
    path = tmp_path / "mementos.db"
    repos = create_app(
        storage=request.param, database_path=path
    ).state.context.repositories
    user = repos.users.add(
        NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash")
    )
    return request.param, path, repos, user


def test_workout_memento_creation_and_restoration():
    workout = Workout(7, 3, "Peito", "Supino")
    memento = workout.create_memento()
    assert memento == WorkoutMemento("Peito", "Supino")
    assert memento.to_update() == WorkoutUpdate("Peito", "Supino")
    with pytest.raises(FrozenInstanceError):
        memento.name = "Mutação"

    updated = Workout(7, 3, "Costas", "Remada")
    restored = updated.restore(memento)
    assert restored == Workout(7, 3, "Peito", "Supino")
    assert updated == Workout(7, 3, "Costas", "Remada")
    with pytest.raises(TypeError, match="Memento"):
        updated.restore("invalido")


@pytest.mark.parametrize(
    "name,description,message",
    [
        ("", "", "Nome do treino"),
        ("   ", "", "Nome do treino"),
        ("a" * 101, "", "Nome do treino"),
        (None, "", "Nome do treino"),
        (123, "", "Nome do treino"),
        ("Peito", "a" * 1001, "Descrição do treino"),
        ("Peito", None, "Descrição do treino"),
        ("Peito", 123, "Descrição do treino"),
    ],
)
def test_workout_memento_rejects_invalid_fields(name, description, message):
    with pytest.raises(InvalidWorkoutError, match=message):
        WorkoutMemento(name, description)


def test_workout_memento_accepts_maximum_field_lengths():
    memento = WorkoutMemento("a" * 100, "b" * 1000)
    assert len(memento.name) == 100
    assert len(memento.description) == 1000


def test_memento_lifecycle_replace_consume_delete_and_independence(configured):
    _, _, repos, user = configured
    first = repos.workouts.add(WorkoutRegistration(user.id, "Peito", "Supino"))
    second = repos.workouts.add(WorkoutRegistration(user.id, "Pernas", "Agachamento"))

    assert repos.mementos.get(first.id) is None
    assert repos.mementos.consume(first.id) is None
    assert repos.mementos.delete(first.id) is False

    initial = first.create_memento()
    repos.mementos.save(first.id, initial)
    assert repos.mementos.get(first.id) == initial
    assert repos.mementos.get(first.id) == initial
    assert repos.mementos.get(second.id) is None

    same_values = WorkoutMemento("Peito", "Supino")
    repos.mementos.save(first.id, same_values)
    assert repos.mementos.get(first.id) == same_values

    replacement = WorkoutMemento("Costas", "Remada")
    repos.mementos.save(first.id, replacement)
    assert repos.mementos.get(first.id) == replacement

    second_memento = second.create_memento()
    repos.mementos.save(second.id, second_memento)

    assert repos.mementos.consume(first.id) == replacement
    assert repos.mementos.consume(first.id) is None
    assert repos.mementos.get(first.id) is None
    assert repos.mementos.delete(first.id) is False
    assert repos.mementos.get(second.id) == second_memento

    after_consume = WorkoutMemento("Ombros", "Desenvolvimento")
    repos.mementos.save(first.id, after_consume)
    assert repos.mementos.get(first.id) == after_consume

    assert repos.mementos.delete(second.id) is True
    assert repos.mementos.get(second.id) is None
    assert repos.mementos.delete(second.id) is False


def test_memento_repository_validates_inputs_and_handles_invalid_ids(configured):
    storage, _, repos, user = configured
    first = repos.workouts.add(WorkoutRegistration(user.id, "Peito", "Supino"))
    assert first.id == 1
    saved = first.create_memento()
    repos.mementos.save(first.id, saved)

    for invalid_id in (0, -1, True, False, "1", None):
        with pytest.raises(InvalidWorkoutError, match="ID do treino"):
            repos.mementos.save(invalid_id, WorkoutMemento("Outro", ""))
        assert repos.mementos.get(invalid_id) is None
        assert repos.mementos.consume(invalid_id) is None
        assert repos.mementos.delete(invalid_id) is False

    assert repos.mementos.get(first.id) == saved

    with pytest.raises(TypeError, match="Memento"):
        repos.mementos.save(first.id, "invalido")
    assert repos.mementos.get(first.id) == saved

    huge = 10**100
    assert repos.mementos.get(huge) is None
    assert repos.mementos.consume(huge) is None
    assert repos.mementos.delete(huge) is False

    if storage == "sqlite":
        for missing_id in (999, huge):
            with pytest.raises(WorkoutNotFoundError):
                repos.mementos.save(missing_id, WorkoutMemento("Outro", ""))


def test_memento_survives_restart_only_in_sqlite(configured):
    storage, path, repos, user = configured
    workout = repos.workouts.add(WorkoutRegistration(user.id, "Antes", "Supino"))
    memento = workout.create_memento()
    repos.mementos.save(workout.id, memento)

    reopened = create_app(
        storage=storage, database_path=path
    ).state.context.repositories
    if storage == "sqlite":
        assert reopened.mementos.get(workout.id) == memento
        assert reopened.mementos.consume(workout.id) == memento
        third = create_app(
            storage=storage, database_path=path
        ).state.context.repositories
        assert third.mementos.get(workout.id) is None
    else:
        assert reopened.mementos.get(workout.id) is None


def test_memento_isolation_across_memory_and_sqlite_instances(tmp_path):
    mem_a = create_app(storage="memory").state.context.repositories
    mem_b = create_app(storage="memory").state.context.repositories
    user_a = mem_a.users.add(
        NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash")
    )
    workout_a = mem_a.workouts.add(WorkoutRegistration(user_a.id, "Peito", "Supino"))
    mem_a.mementos.save(workout_a.id, workout_a.create_memento())
    assert mem_b.mementos.get(workout_a.id) is None

    db_first = create_app(
        storage="sqlite", database_path=tmp_path / "first.db"
    ).state.context.repositories
    db_second = create_app(
        storage="sqlite", database_path=tmp_path / "second.db"
    ).state.context.repositories
    user_sql = db_first.users.add(
        NewUser("joao", "joao@example.com", UserRole.STUDENT, "hash")
    )
    workout_sql = db_first.workouts.add(
        WorkoutRegistration(user_sql.id, "Costas", "Remada")
    )
    db_first.mementos.save(workout_sql.id, workout_sql.create_memento())
    assert db_second.mementos.get(workout_sql.id) is None

    shared_path = tmp_path / "shared.db"
    app_a = create_app(
        storage="sqlite", database_path=shared_path
    ).state.context.repositories
    app_b = create_app(
        storage="sqlite", database_path=shared_path
    ).state.context.repositories
    shared_user = app_a.users.add(
        NewUser("ana", "ana@example.com", UserRole.STUDENT, "hash")
    )
    shared_workout = app_a.workouts.add(
        WorkoutRegistration(shared_user.id, "Original", "Desc")
    )
    app_a.mementos.save(shared_workout.id, shared_workout.create_memento())
    assert app_b.mementos.get(shared_workout.id) == WorkoutMemento("Original", "Desc")
    assert app_b.mementos.consume(shared_workout.id) == WorkoutMemento(
        "Original", "Desc"
    )
    assert app_a.mementos.get(shared_workout.id) is None


def test_sqlite_existing_database_preserved_without_fabricating_mementos(tmp_path):
    path = tmp_path / "legacy.db"
    initial = create_app(
        storage="sqlite", database_path=path
    ).state.context.repositories
    user = initial.users.add(
        NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash")
    )
    now = datetime(2026, 11, 24, 10, 0, tzinfo=UTC)
    with initial.unit_of_work.transaction() as tx:
        workout = tx.workouts.add(WorkoutRegistration(user.id, "Legado", "Texto"))
        tx.accesses.add(AccessEvent(user.id, "create", now))

    with sqlite3.connect(path) as db:
        db.execute("DROP TABLE workout_mementos")

    reopened = create_app(
        storage="sqlite", database_path=path
    ).state.context.repositories
    assert reopened.users.get_by_id(user.id) == user
    assert reopened.workouts.get_by_id(workout.id) == workout
    assert reopened.accesses.list_between(now, now + timedelta(seconds=1)) == [
        AccessEvent(user.id, "create", now)
    ]
    assert reopened.mementos.get(workout.id) is None
    assert reopened.mementos.consume(workout.id) is None

    reopened.mementos.save(workout.id, workout.create_memento())
    assert reopened.mementos.consume(workout.id) == WorkoutMemento("Legado", "Texto")


def test_sqlite_deleting_workout_cascades_memento(tmp_path):
    path = tmp_path / "cascade.db"
    repos = create_app(storage="sqlite", database_path=path).state.context.repositories
    user = repos.users.add(
        NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash")
    )
    workout = repos.workouts.add(WorkoutRegistration(user.id, "Peito", "Supino"))
    repos.mementos.save(workout.id, workout.create_memento())

    assert repos.workouts.delete(workout.id) is True
    assert repos.mementos.get(workout.id) is None
    with sqlite3.connect(path) as db:
        count = db.execute("SELECT COUNT(*) FROM workout_mementos").fetchone()[0]
    assert count == 0


def test_uow_capture_and_replacement_commit_and_rollback(configured):
    _, _, repos, user = configured
    workout = repos.workouts.add(WorkoutRegistration(user.id, "Original", "Desc 0"))
    first_event_time = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
    second_event_time = first_event_time + timedelta(minutes=1)

    with pytest.raises(RuntimeError):
        with repos.unit_of_work.transaction() as tx:
            tx.mementos.save(workout.id, workout.create_memento())
            tx.workouts.update(workout.id, WorkoutUpdate("Edição 1", "Desc 1"))
            tx.accesses.add(AccessEvent(user.id, "update", first_event_time))
            raise RuntimeError("falha na captura inicial")

    assert repos.workouts.get_by_id(workout.id) == workout
    assert repos.mementos.get(workout.id) is None
    assert (
        repos.accesses.list_between(
            first_event_time - timedelta(seconds=1),
            second_event_time + timedelta(seconds=1),
        )
        == []
    )

    with repos.unit_of_work.transaction() as tx:
        current = tx.workouts.get_by_id(workout.id)
        tx.mementos.save(workout.id, current.create_memento())
        updated = tx.workouts.update(workout.id, WorkoutUpdate("Edição 1", "Desc 1"))
        tx.accesses.add(AccessEvent(user.id, "update", first_event_time))

    assert updated == Workout(workout.id, user.id, "Edição 1", "Desc 1")
    assert repos.workouts.get_by_id(workout.id) == updated
    assert repos.mementos.get(workout.id) == WorkoutMemento("Original", "Desc 0")

    with pytest.raises(RuntimeError):
        with repos.unit_of_work.transaction() as tx:
            current = tx.workouts.get_by_id(workout.id)
            tx.mementos.save(workout.id, current.create_memento())
            tx.workouts.update(workout.id, WorkoutUpdate("Edição 2", "Desc 2"))
            tx.accesses.add(AccessEvent(user.id, "update", second_event_time))
            raise RuntimeError("falha na substituição")

    assert repos.workouts.get_by_id(workout.id) == updated
    assert repos.mementos.get(workout.id) == WorkoutMemento("Original", "Desc 0")
    assert repos.accesses.list_between(
        first_event_time, second_event_time + timedelta(seconds=1)
    ) == [AccessEvent(user.id, "update", first_event_time)]


def test_uow_consume_and_delete_commit_and_rollback(configured):
    _, _, repos, user = configured
    workout = repos.workouts.add(WorkoutRegistration(user.id, "Antes", "Supino"))
    memento = workout.create_memento()
    repos.mementos.save(workout.id, memento)
    updated = repos.workouts.update(workout.id, WorkoutUpdate("Depois", "Remada"))
    event_time = datetime(2026, 11, 24, 13, 0, tzinfo=UTC)

    with pytest.raises(RuntimeError):
        with repos.unit_of_work.transaction() as tx:
            consumed = tx.mementos.consume(workout.id)
            assert consumed == memento
            tx.workouts.update(workout.id, consumed.to_update())
            tx.accesses.add(AccessEvent(user.id, "update", event_time))
            raise RuntimeError("falha no consumo")

    assert repos.workouts.get_by_id(workout.id) == updated
    assert repos.mementos.get(workout.id) == memento
    assert (
        repos.accesses.list_between(event_time, event_time + timedelta(seconds=1)) == []
    )

    with repos.unit_of_work.transaction() as tx:
        consumed = tx.mementos.consume(workout.id)
        assert consumed is not None
        current = tx.workouts.get_by_id(workout.id)
        restored = current.restore(consumed)
        tx.workouts.update(workout.id, restored.create_memento().to_update())
        tx.accesses.add(AccessEvent(user.id, "update", event_time))

    assert repos.workouts.get_by_id(workout.id) == Workout(
        workout.id, user.id, "Antes", "Supino"
    )
    assert repos.mementos.get(workout.id) is None

    repos.mementos.save(workout.id, WorkoutMemento("Outro", "Desc"))
    delete_time = event_time + timedelta(minutes=1)

    with pytest.raises(RuntimeError):
        with repos.unit_of_work.transaction() as tx:
            assert tx.mementos.delete(workout.id) is True
            assert tx.workouts.delete(workout.id) is True
            tx.accesses.add(AccessEvent(user.id, "delete", delete_time))
            raise RuntimeError("falha na exclusão")

    assert repos.workouts.get_by_id(workout.id) == Workout(
        workout.id, user.id, "Antes", "Supino"
    )
    assert repos.mementos.get(workout.id) == WorkoutMemento("Outro", "Desc")
    assert (
        repos.accesses.list_between(delete_time, delete_time + timedelta(seconds=1))
        == []
    )

    with repos.unit_of_work.transaction() as tx:
        assert tx.mementos.delete(workout.id) is True
        assert tx.workouts.delete(workout.id) is True
        tx.accesses.add(AccessEvent(user.id, "delete", delete_time))

    assert repos.workouts.get_by_id(workout.id) is None
    assert repos.mementos.get(workout.id) is None
    assert repos.accesses.list_between(
        delete_time, delete_time + timedelta(seconds=1)
    ) == [AccessEvent(user.id, "delete", delete_time)]


def test_sqlite_memento_initialization_failure_is_safe(tmp_path):
    with pytest.raises(PersistenceError) as caught:
        SQLiteWorkoutMementoRepository(tmp_path / "missing" / "db.sqlite")
    assert caught.value.public_message == PersistenceError.WORKOUT_MESSAGE
    assert isinstance(caught.value.__cause__, sqlite3.Error)


def test_sqlite_memento_table_missing_or_trigger_failure_rolls_back_transaction(
    tmp_path,
):
    path = tmp_path / "trigger.db"
    repos = create_app(storage="sqlite", database_path=path).state.context.repositories
    user = repos.users.add(
        NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash")
    )
    workout = repos.workouts.add(WorkoutRegistration(user.id, "Inicial", "D0"))
    now = datetime(2026, 11, 24, 14, 0, tzinfo=UTC)

    with sqlite3.connect(path) as db:
        db.execute("DROP TABLE workout_mementos")

    with pytest.raises(PersistenceError) as caught:
        with repos.unit_of_work.transaction() as tx:
            tx.workouts.update(workout.id, WorkoutUpdate("Alterado", "D1"))
            tx.mementos.save(workout.id, workout.create_memento())
            tx.accesses.add(AccessEvent(user.id, "update", now))
    assert caught.value.public_message == PersistenceError.WORKOUT_MESSAGE
    assert repos.workouts.get_by_id(workout.id) == workout
    assert repos.accesses.list_between(now, now + timedelta(seconds=1)) == []

    repos = create_app(storage="sqlite", database_path=path).state.context.repositories
    initial_memento = WorkoutMemento("Inicial", "D0")
    repos.mementos.save(workout.id, initial_memento)

    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TRIGGER fail_memento_update BEFORE UPDATE ON workout_mementos "
            "BEGIN SELECT RAISE(ABORT, 'private memento update failure'); END"
        )

    with pytest.raises(PersistenceError) as caught:
        with repos.unit_of_work.transaction() as tx:
            tx.workouts.update(workout.id, WorkoutUpdate("Alterado", "D1"))
            tx.mementos.save(workout.id, WorkoutMemento("Outro", "D2"))
            tx.accesses.add(AccessEvent(user.id, "update", now))
    assert caught.value.public_message == PersistenceError.WORKOUT_MESSAGE
    assert repos.workouts.get_by_id(workout.id) == workout
    assert repos.mementos.get(workout.id) == initial_memento
    assert repos.accesses.list_between(now, now + timedelta(seconds=1)) == []

    with sqlite3.connect(path) as db:
        db.execute("DROP TRIGGER fail_memento_update")
        db.execute(
            "CREATE TRIGGER fail_memento_delete BEFORE DELETE ON workout_mementos "
            "BEGIN SELECT RAISE(ABORT, 'private memento delete failure'); END"
        )

    with pytest.raises(PersistenceError) as caught:
        with repos.unit_of_work.transaction() as tx:
            tx.mementos.consume(workout.id)
            tx.workouts.update(workout.id, WorkoutUpdate("Alterado", "D1"))
            tx.accesses.add(AccessEvent(user.id, "update", now))
    assert caught.value.public_message == PersistenceError.WORKOUT_MESSAGE
    assert repos.workouts.get_by_id(workout.id) == workout
    assert repos.mementos.get(workout.id) == initial_memento
    assert repos.accesses.list_between(now, now + timedelta(seconds=1)) == []


@pytest.mark.parametrize("mode", ["save", "replace", "consume", "delete"])
def test_sqlite_deferred_commit_failure_rolls_back_memento(tmp_path, mode):
    path = tmp_path / "commit_fail.db"
    repos = create_app(storage="sqlite", database_path=path).state.context.repositories
    user = repos.users.add(
        NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash")
    )
    workout = repos.workouts.add(WorkoutRegistration(user.id, "Original", "D0"))
    previous = WorkoutMemento("Anterior", "Prev")
    if mode in ("replace", "consume", "delete"):
        repos.mementos.save(workout.id, previous)
    now = datetime(2026, 11, 24, 15, 0, tzinfo=UTC)

    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TABLE pending (user_id INTEGER REFERENCES users(id) DEFERRABLE INITIALLY DEFERRED)"
        )
        db.execute(
            "CREATE TRIGGER fail_event_commit AFTER INSERT ON access_events "
            "BEGIN INSERT INTO pending VALUES (999); END"
        )

    with pytest.raises(PersistenceError) as caught:
        with repos.unit_of_work.transaction() as tx:
            if mode == "save":
                tx.mementos.save(workout.id, workout.create_memento())
                tx.workouts.update(workout.id, WorkoutUpdate("Novo", "D1"))
                tx.accesses.add(AccessEvent(user.id, "update", now))
            elif mode == "replace":
                tx.mementos.save(workout.id, WorkoutMemento("Substituto", "D2"))
                tx.workouts.update(workout.id, WorkoutUpdate("Novo", "D1"))
                tx.accesses.add(AccessEvent(user.id, "update", now))
            elif mode == "consume":
                consumed = tx.mementos.consume(workout.id)
                assert consumed == previous
                tx.workouts.update(workout.id, consumed.to_update())
                tx.accesses.add(AccessEvent(user.id, "update", now))
            else:
                assert tx.mementos.delete(workout.id) is True
                assert tx.workouts.delete(workout.id) is True
                tx.accesses.add(AccessEvent(user.id, "delete", now))

    assert caught.value.public_message == PersistenceError.WORKOUT_MESSAGE
    assert repos.workouts.get_by_id(workout.id) == workout
    assert repos.mementos.get(workout.id) == (None if mode == "save" else previous)
    assert repos.accesses.list_between(now, now + timedelta(seconds=1)) == []


def test_sqlite_unit_of_work_lock_conflict_raises_persistence_error_without_partial_state(
    tmp_path, monkeypatch
):
    path = tmp_path / "locked.db"
    repos = create_app(storage="sqlite", database_path=path).state.context.repositories
    user = repos.users.add(
        NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash")
    )
    workout = repos.workouts.add(WorkoutRegistration(user.id, "Inicial", "Desc"))

    locker = sqlite3.connect(path, isolation_level=None)
    try:
        locker.execute("BEGIN IMMEDIATE")
        real_connect = sqlite3.connect
        monkeypatch.setattr(
            "app.storage.sqlite3.connect",
            lambda *args, **kwargs: real_connect(*args, **{**kwargs, "timeout": 0.05}),
        )
        with pytest.raises(PersistenceError) as caught:
            with repos.unit_of_work.transaction() as tx:
                tx.mementos.save(workout.id, workout.create_memento())
                tx.workouts.update(workout.id, WorkoutUpdate("Novo", "Desc"))
        assert caught.value.public_message == PersistenceError.WORKOUT_MESSAGE
    finally:
        locker.execute("ROLLBACK")
        locker.close()

    monkeypatch.undo()
    assert repos.workouts.get_by_id(workout.id) == workout
    assert repos.mementos.get(workout.id) is None


def test_concurrent_consume_allows_at_most_one_restoration(configured):
    _, _, repos, user = configured
    workout = repos.workouts.add(WorkoutRegistration(user.id, "Atual", "Desc atual"))
    memento = WorkoutMemento("Anterior", "Desc anterior")
    repos.mementos.save(workout.id, memento)
    now = datetime(2026, 11, 24, 16, 0, tzinfo=UTC)

    workers = 8
    barrier = Barrier(workers)

    def try_consume(_: int) -> WorkoutMemento | None:
        barrier.wait(timeout=5)
        with repos.unit_of_work.transaction() as tx:
            consumed = tx.mementos.consume(workout.id)
            if consumed is not None:
                tx.workouts.update(workout.id, consumed.to_update())
                tx.accesses.add(AccessEvent(user.id, "update", now))
            return consumed

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(try_consume, range(workers)))

    assert results.count(memento) == 1
    assert results.count(None) == workers - 1
    assert repos.workouts.get_by_id(workout.id) == Workout(
        workout.id, user.id, "Anterior", "Desc anterior"
    )
    assert repos.mementos.get(workout.id) is None
    assert repos.accesses.list_between(now, now + timedelta(seconds=1)) == [
        AccessEvent(user.id, "update", now)
    ]


def test_concurrent_save_and_consume_are_serializable(configured):
    _, _, repos, user = configured
    now = datetime(2026, 11, 24, 17, 0, tzinfo=UTC)

    for round_index in range(10):
        workout = repos.workouts.add(WorkoutRegistration(user.id, "Estado 1", "D1"))
        repos.mementos.save(workout.id, WorkoutMemento("Estado 0", "D0"))
        barrier = Barrier(2)

        def run_update(
            workout_id: int = workout.id, round_barrier: Barrier = barrier
        ) -> None:
            round_barrier.wait(timeout=5)
            with repos.unit_of_work.transaction() as tx:
                current = tx.workouts.get_by_id(workout_id)
                assert current is not None
                tx.mementos.save(workout_id, current.create_memento())
                tx.workouts.update(workout_id, WorkoutUpdate("Estado 2", "D2"))
                tx.accesses.add(AccessEvent(user.id, "update", now))

        def run_undo(
            workout_id: int = workout.id, round_barrier: Barrier = barrier
        ) -> None:
            round_barrier.wait(timeout=5)
            with repos.unit_of_work.transaction() as tx:
                consumed = tx.mementos.consume(workout_id)
                if consumed is not None:
                    tx.workouts.update(workout_id, consumed.to_update())
                    tx.accesses.add(AccessEvent(user.id, "update", now))

        with ThreadPoolExecutor(max_workers=2) as executor:
            update_future = executor.submit(run_update)
            undo_future = executor.submit(run_undo)
            update_future.result()
            undo_future.result()

        final_workout = repos.workouts.get_by_id(workout.id)
        final_memento = repos.mementos.get(workout.id)
        assert final_workout is not None
        observed = (
            final_workout.name,
            final_workout.description,
            final_memento.name if final_memento is not None else None,
            final_memento.description if final_memento is not None else None,
        )
        # Either undo ran first (leaving Estado 0 -> Estado 2) or update ran first (leaving Estado 1, None).
        assert observed in (
            ("Estado 2", "D2", "Estado 0", "D0"),
            ("Estado 1", "D1", None, None),
        ), f"Estado não serializável na rodada {round_index}: {observed}"
