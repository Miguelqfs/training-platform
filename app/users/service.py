from app.users.credentials import hash_password, validate_credentials
from app.users.domain import User, UserRole
from app.users.repository import MemoryUserRepository, UserRepository


class UserService:
    def __init__(self, repository: UserRepository | None = None) -> None:
        self._repository = (
            repository if repository is not None else MemoryUserRepository()
        )

    def add_user(
        self, username: str, email: str, role: UserRole, password: str
    ) -> User:
        username = username.strip()
        email = email.strip().lower()
        validate_credentials(username, email, password)
        return self._repository.add(username, email, role, hash_password(password))

    def list_users(self) -> list[User]:
        return self._repository.list_users()
