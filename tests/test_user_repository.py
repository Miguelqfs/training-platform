import pytest

from app.users.domain import NewUser, UserRole
from app.users.repository import MemoryUserRepository, SQLiteUserRepository
from app.users.service import UserService


@pytest.mark.parametrize("storage", ["memory", "sqlite"])
def test_real_user_repositories_find_and_count_users(storage, tmp_path):
    users = (
        MemoryUserRepository()
        if storage == "memory"
        else SQLiteUserRepository(tmp_path / "users.db")
    )
    assert users.count() == 0
    assert users.get_by_id(999) is None
    user = users.add(NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash"))
    assert users.get_by_id(user.id) == user
    assert UserService(users).count_users() == 1


@pytest.mark.parametrize("storage", ["memory", "sqlite"])
def test_legacy_user_factory_remains_usable(storage, tmp_path, monkeypatch):
    from app.users.factory import create_user_repository

    monkeypatch.setenv("USER_STORAGE", "unknown")
    repository = create_user_repository(storage, tmp_path / "factory.db")
    assert repository.count() == 0
    user = repository.add(
        NewUser("maria", "maria@example.com", UserRole.STUDENT, "hash")
    )
    assert repository.get_by_id(user.id) == user
    assert repository.list_users() == [user]
