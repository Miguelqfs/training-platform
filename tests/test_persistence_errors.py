import pytest

from app.users.domain import PersistenceError


def test_persistence_error_never_accepts_arbitrary_public_text():
    assert (
        PersistenceError("SQL private").public_message == PersistenceError.USER_MESSAGE
    )
    assert str(PersistenceError("SQL private")) == "SQL private"
    with pytest.raises(ValueError, match="Mensagem pública"):
        PersistenceError("private", public_message="SQL private")
