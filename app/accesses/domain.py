from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

Operation = Literal["create", "get", "update", "delete"]


def utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Instante deve ter fuso explícito")
    return value.astimezone(UTC)


def interval(start: datetime, end: datetime) -> tuple[datetime, datetime]:
    start, end = utc(start), utc(end)
    if start >= end:
        raise ValueError("Início deve ser anterior ao fim")
    return start, end


@dataclass(frozen=True)
class AccessEvent:
    user_id: int
    operation: Operation
    occurred_at: datetime

    def __post_init__(self) -> None:
        if type(self.user_id) is not int or self.user_id < 1:
            raise ValueError("Identificador de usuário inválido")
        if self.operation not in ("create", "get", "update", "delete"):
            raise ValueError("Operação inválida")
        object.__setattr__(self, "occurred_at", utc(self.occurred_at))
