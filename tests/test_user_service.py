from app.users.domain import NewUser, User, UserRegistration, UserRole
from app.users.service import UserService


def test_service_accepts_an_independent_repository() -> None:
    class SubstituteRepository:
        def __init__(self) -> None:
            self.users: list[User] = []

        def add(self, data: NewUser) -> User:
            user = User(
                id=42,
                username=data.username,
                email=data.email,
                role=data.role,
                password_hash=data.password_hash,
            )
            self.users.append(user)
            return user

        def list_users(self) -> list[User]:
            return list(self.users)

    service = UserService(SubstituteRepository())
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
