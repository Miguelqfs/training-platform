import hashlib
import secrets
import string

from app.users.domain import InvalidLoginError, InvalidPasswordError
from app.users.policy import (
    IAM_SYMBOLS,
    MAX_LOGIN_LENGTH,
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_CATEGORIES,
    MIN_PASSWORD_LENGTH,
    PASSWORD_HASH_ITERATIONS,
    PASSWORD_SALT_BYTES,
)


def validate_credentials(username: str, email: str, password: str) -> None:
    validate_login(username)
    validate_password(password)
    normalized_password = password.casefold()
    if normalized_password in (username.casefold(), email.casefold()):
        raise InvalidPasswordError("Senha não pode ser igual ao login ou e-mail")


def validate_login(username: str) -> None:
    if not username:
        raise InvalidLoginError("Login não pode ser vazio")
    if len(username) > MAX_LOGIN_LENGTH:
        raise InvalidLoginError(
            f"Login deve ter no máximo {MAX_LOGIN_LENGTH} caracteres"
        )
    if any(character.isnumeric() for character in username):
        raise InvalidLoginError("Login não pode conter números")


def validate_password(password: str) -> None:
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise InvalidPasswordError(
            f"Senha deve ter de {MIN_PASSWORD_LENGTH} a {MAX_PASSWORD_LENGTH} caracteres"
        )
    categories = (
        string.ascii_uppercase,
        string.ascii_lowercase,
        string.digits,
        IAM_SYMBOLS,
    )
    category_count = sum(
        any(character in category for character in password) for category in categories
    )
    if category_count < MIN_PASSWORD_CATEGORIES:
        raise InvalidPasswordError(
            f"Senha deve conter pelo menos {MIN_PASSWORD_CATEGORIES} categorias: "
            "maiúsculas, minúsculas, números ou símbolos IAM"
        )


def hash_password(password: str) -> str:
    salt = secrets.token_hex(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), PASSWORD_HASH_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${salt}${digest.hex()}"
