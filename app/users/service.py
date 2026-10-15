from app.users.credentials import hash_password, validate_credentials
from app.users.domain import NewUser, User, UserRegistration
from app.users.repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def add_user(self, registration: UserRegistration) -> User:
        username = registration.username.strip()
        email = registration.email.strip().lower()
        validate_credentials(username, email, registration.password)
        return self._repository.add(
            NewUser(
                username=username,
                email=email,
                role=registration.role,
                password_hash=hash_password(registration.password),
            )
        )

    def list_users(self) -> list[User]:
        return self._repository.list_users()
