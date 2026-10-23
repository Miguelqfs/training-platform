import pytest

from app.users.domain import UserRole
from app.workouts.domain import (
    UserNotFoundError,
    Workout,
    WorkoutRegistration,
    WorkoutUpdate,
)
from app.workouts.service import WorkoutService


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
