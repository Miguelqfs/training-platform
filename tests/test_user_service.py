from app.users.domain import NewUser, User, UserRegistration, UserRole
from app.users.service import UserService


def test_service_accepts_an_independent_repository() -> None:
    class SubstituteRepository:
        def __init__(self) -> None:
            self.users: list[User] = []

        def add(self, data: NewUser) -> User:
            user = User(
                id=42 + len(self.users),
                username=data.username,
                email=data.email,
                role=data.role,
                password_hash=data.password_hash,
            )
            self.users.append(user)
            return user

        def list_users(self) -> list[User]:
            return list(self.users)

        def get_by_id(self, user_id: int) -> User | None:
            return next((user for user in self.users if user.id == user_id), None)

        def count(self) -> int:
            return len(self.users)

    repository = SubstituteRepository()
    service = UserService(repository)
    user = service.add_user(
        UserRegistration(
            username=" Maria ",
            email="MARIA@example.com",
            role=UserRole.STUDENT,
            password="Abcdef12",
        )
    )

    assert user.id == 42
    assert user.username == "Maria"
    assert user.email == "maria@example.com"
    assert user.password_hash.startswith("pbkdf2_sha256$")
    assert service.list_users() == [user]
    assert repository.get_by_id(42) == user
    assert repository.get_by_id(999) is None
    assert service.count_users() == 1
    second = service.add_user(
        UserRegistration("ana", "ana@example.com", UserRole.ADMIN, "Abcdef12")
    )
    assert repository.get_by_id(42) == user
    assert repository.get_by_id(43) == second
    assert service.count_users() == 2
    assert service.list_users() == [user, second]
