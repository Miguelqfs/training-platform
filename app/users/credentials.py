import hashlib
import secrets
import string

from app.users.domain import InvalidCredentialsError

IAM_SYMBOLS = "!@#$%^&*()_+-=[]{}|'"


def validate_credentials(username: str, email: str, password: str) -> None:
    if not username or len(username) > 12 or any(c.isnumeric() for c in username):
        raise InvalidCredentialsError(
            "Login deve ter entre 1 e 12 caracteres e não conter números"
        )
    categories = (
        string.ascii_uppercase,
        string.ascii_lowercase,
        string.digits,
        IAM_SYMBOLS,
    )
    if (
        not 8 <= len(password) <= 128
        or sum(any(c in category for c in password) for category in categories) < 3
    ):
        raise InvalidCredentialsError(
            "Senha deve ter de 8 a 128 caracteres e três categorias: maiúsculas, minúsculas, números ou símbolos IAM"
        )
    if password in (username, email):
        raise InvalidCredentialsError("Senha não pode ser igual ao login ou e-mail")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 600_000
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"
