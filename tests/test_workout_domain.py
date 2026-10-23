import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

from app.storage import sqlite_connection
from app.users.domain import NewUser, PersistenceError, UserRole
from app.users.repository import MemoryUserRepository, SQLiteUserRepository
from app.workouts.domain import (
    InvalidWorkoutError,
    UserNotFoundError,
    Workout,
    WorkoutNotFoundError,
    WorkoutRegistration,
    WorkoutUpdate,
)
from app.workouts.repository import MemoryWorkoutRepository, SQLiteWorkoutRepository
from app.workouts.service import WorkoutService


@pytest.fixture(params=["memory", "sqlite"])
def repositories(request, tmp_path):
    path = tmp_path / "domain.db"
    users = (
        MemoryUserRepository()
        if request.param == "memory"
        else SQLiteUserRepository(path)
    )
    workouts = (
        MemoryWorkoutRepository()
        if request.param == "memory"
        else SQLiteWorkoutRepository(path)
    )
    return users, workouts


def test_workout_repository_contract(repositories):
    users, workouts = repositories
    user = users.add(NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash"))
    assert workouts.count() == 0
    assert workouts.get_by_id(999) is None
    assert workouts.update(999, WorkoutUpdate("Novo")) is None
    assert workouts.delete(999) is False
    data = WorkoutRegistration(user.id, "Plano", "Texto")
    first, second = workouts.add(data), workouts.add(data)
    assert workouts.list_workouts() == [first, second]
    updated = workouts.update(first.id, WorkoutUpdate("Novo", "Outro"))
    assert updated == Workout(first.id, user.id, "Novo", "Outro")
    assert first.name == data.name == "Plano"
    assert workouts.delete(second.id)
    assert workouts.add(data).id > second.id
    assert workouts.count() == 2
    with pytest.raises(FrozenInstanceError):
        updated.name = "Mutação"


@pytest.mark.parametrize("user_id", [True, False, 0, -1, 1.0, "1", None])
def test_service_validates_id_before_fields_or_lookup(repositories, user_id):
    users, workouts = repositories
    service = WorkoutService(workouts, users)
    with pytest.raises(
        InvalidWorkoutError, match="ID do usuário deve ser um inteiro positivo"
    ):
        service.create_workout(WorkoutRegistration(user_id, "", None))
    with pytest.raises(
        InvalidWorkoutError, match="ID do treino deve ser um inteiro positivo"
    ):
        service.update_workout(user_id, WorkoutUpdate("", None))
    for method in (service.get_workout, service.delete_workout):
        with pytest.raises(InvalidWorkoutError, match="ID do treino"):
            method(user_id)
    assert workouts.count() == 0


@pytest.mark.parametrize(
    "case",
    [
        (" ", None, "Nome do treino"),
        (None, "", "Nome do treino"),
        (False, "", "Nome do treino"),
        ("á" * 101, "", "Nome do treino"),
        ("Plano", None, "Descrição do treino"),
        ("Plano", 1, "Descrição do treino"),
        ("Plano", "á" * 1001, "Descrição do treino"),
    ],
)
def test_service_validates_fields_before_missing_records(repositories, case):
    name, description, message = case
    users, workouts = repositories
    service = WorkoutService(workouts, users)
    with pytest.raises(InvalidWorkoutError, match=message):
        service.create_workout(WorkoutRegistration(999, name, description))
    with pytest.raises(InvalidWorkoutError, match=message):
        service.update_workout(999, WorkoutUpdate(name, description))
    assert workouts.count() == 0


def test_service_handles_normalization_and_missing_records(repositories):
    users, workouts = repositories
    service = WorkoutService(workouts, users)
    with pytest.raises(UserNotFoundError):
        service.create_workout(WorkoutRegistration(1, "Plano"))
    users.add(NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash"))
    workout = service.create_workout(WorkoutRegistration(1, " á ", " texto "))
    assert workout == Workout(1, 1, "á", "texto")
    assert service.get_workout(workout.id) == workout
    assert service.update_workout(workout.id, WorkoutUpdate(" Novo ")) == Workout(
        1, 1, "Novo", ""
    )
    service.delete_workout(workout.id)
    for method in (service.get_workout, service.delete_workout):
        with pytest.raises(WorkoutNotFoundError):
            method(workout.id)
    with pytest.raises(WorkoutNotFoundError):
        service.update_workout(workout.id, WorkoutUpdate("Nome"))
    assert service.list_workouts() == []
    assert service.count_workouts() == 0


def test_memory_concurrent_ids_never_collide_or_reuse_deleted_highest():
    repository = MemoryWorkoutRepository()
    users = MemoryUserRepository()
    users.add(NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash"))
    service = WorkoutService(repository, users)
    with ThreadPoolExecutor(max_workers=16) as executor:
        workouts = list(
            executor.map(
                lambda _: service.create_workout(WorkoutRegistration(1, "Plano")),
                range(100),
            )
        )
    assert sorted(w.id for w in workouts) == list(range(1, 101))
    assert repository.delete(100)
    assert repository.delete(1)
    assert repository.add(WorkoutRegistration(1, "Novo")).id == 101
    assert repository.count() == 99


def test_foreign_keys_on_each_connection_and_only_fk_is_missing_user(tmp_path):
    path = tmp_path / "foreign.db"
    users = SQLiteUserRepository(path)
    workouts = SQLiteWorkoutRepository(path)
    for _ in range(2):
        with sqlite_connection(path) as connection:
            assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
    with pytest.raises(UserNotFoundError):
        workouts.add(WorkoutRegistration(999, "Órfão"))
    users.add(NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash"))
    with pytest.raises(PersistenceError) as caught:
        workouts.add(WorkoutRegistration(1, None))
    assert isinstance(caught.value.__cause__, sqlite3.IntegrityError)
    assert caught.value.public_message == PersistenceError.WORKOUT_MESSAGE
    assert workouts.count() == 0


def test_workout_initialization_failure_is_safe(tmp_path):
    with pytest.raises(PersistenceError) as caught:
        SQLiteWorkoutRepository(tmp_path / "missing" / "db.sqlite")
    assert caught.value.public_message == PersistenceError.WORKOUT_MESSAGE
    assert isinstance(caught.value.__cause__, sqlite3.Error)


def test_service_accepts_independent_contracts_without_inheritance():
    class Users:
        def add(self, data):
            raise AssertionError("cadastro de usuário inesperado")

        def list_users(self):
            return []

        def get_by_id(self, user_id):
            from app.users.domain import User

            if user_id != 7:
                return None
            return User(user_id, "maria", "maria@example.com", UserRole.STUDENT, "hash")

        def count(self):
            return 1

    class Workouts:
        def __init__(self):
            self.saved = None

        def add(self, data):
            self.saved = Workout(42, data.user_id, data.name, data.description)
            return self.saved

        def get_by_id(self, workout_id):
            return self.saved if self.saved and self.saved.id == workout_id else None

        def list_workouts(self):
            return [self.saved] if self.saved else []

        def update(self, workout_id, data):
            if not self.get_by_id(workout_id):
                return None
            self.saved = Workout(
                workout_id, self.saved.user_id, data.name, data.description
            )
            return self.saved

        def delete(self, workout_id):
            exists = self.get_by_id(workout_id) is not None
            if exists:
                self.saved = None
            return exists

        def count(self):
            return int(self.saved is not None)

    service = WorkoutService(Workouts(), Users())
    workout = service.create_workout(WorkoutRegistration(7, " Plano "))
    assert workout == Workout(42, 7, "Plano", "")
    assert service.get_workout(42) == workout
    assert service.list_workouts() == [workout]
    assert service.count_workouts() == 1
    assert service.update_workout(42, WorkoutUpdate("Novo")).name == "Novo"
    service.delete_workout(42)
    assert service.count_workouts() == 0
    with pytest.raises(UserNotFoundError):
        service.create_workout(WorkoutRegistration(999, "Ausente"))
    assert service.list_workouts() == []


def test_link_lookup_failure_preserves_cause_and_uses_workout_message(monkeypatch):
    users = MemoryUserRepository()
    original = PersistenceError("SQL/private/path")

    def fail(user_id):
        raise original

    monkeypatch.setattr(users, "get_by_id", fail)
    service = WorkoutService(MemoryWorkoutRepository(), users)
    with pytest.raises(PersistenceError) as caught:
        service.create_workout(WorkoutRegistration(1, "Plano"))
    assert caught.value.__cause__ is original
    assert caught.value.public_message == PersistenceError.WORKOUT_MESSAGE


@pytest.mark.parametrize("storage", ["memory", "sqlite"])
def test_arbitrarily_large_ids_are_absent_not_driver_failures(storage, tmp_path):
    from fastapi.testclient import TestClient

    from app.main import create_app

    huge = 10**100
    with TestClient(
        create_app(storage=storage, database_path=tmp_path / "huge.db")
    ) as client:
        response = client.post("/workouts/", json={"user_id": huge, "name": "Plano"})
        assert response.status_code == 404
        for method in ("get", "put", "delete"):
            kwargs = {"json": {"name": "Novo"}} if method == "put" else {}
            response = client.request(method, f"/workouts/{huge}", **kwargs)
            assert response.status_code == 404
        assert client.get("/statistics/entities").json() == {"total": 0}


def test_ids_remain_monotonic_after_deleting_entire_collection(repositories):
    users, workouts = repositories
    user = users.add(NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash"))
    data = WorkoutRegistration(user.id, "Plano")
    first = workouts.add(data)
    assert workouts.delete(first.id)
    assert workouts.count() == 0
    assert workouts.list_workouts() == []
    second = workouts.add(data)
    assert second.id > first.id
    assert users.get_by_id(user.id) == user
    assert workouts.count() == 1
