from threading import Lock

from app.users.domain import DuplicateUserError, User, UserRole


class UserService:
    def __init__(self) -> None:
        self._users: list[User] = []
        self._next_id = 1
        self._lock = Lock()

    def add_user(self, username: str, email: str, role: UserRole) -> User:
        username = username.strip()
        email = email.strip().lower()

        with self._lock:
            if any(
                user.username.casefold() == username.casefold()
                or user.email.casefold() == email.casefold()
                for user in self._users
            ):
                raise DuplicateUserError("Usuário ou e-mail já cadastrado")

            user = User(id=self._next_id, username=username, email=email, role=role)
            self._users.append(user)
            self._next_id += 1
            return user

    def list_users(self) -> list[User]:
        with self._lock:
            return list(self._users)
