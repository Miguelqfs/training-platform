from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.accesses.domain import AccessEvent, Operation

ReportFormat = Literal["html", "pdf"]
OPERATION_ORDER: tuple[Operation, ...] = ("create", "get", "update", "delete")


class InvalidReportError(ValueError):
    pass


class ReportGenerationError(Exception):
    PUBLIC_MESSAGE = "Não foi possível gerar o relatório de acessos"


@dataclass(frozen=True)
class AccessReportRequest:
    start: datetime
    end: datetime
    format: ReportFormat


@dataclass(frozen=True)
class GeneratedReport:
    content: bytes
    media_type: str


@dataclass(frozen=True)
class AccessReport:
    start: datetime
    end: datetime
    total: int
    users: tuple[tuple[int, int], ...]
    operations: tuple[tuple[Operation, int], ...]


def aggregate(
    start: datetime, end: datetime, events: list[AccessEvent]
) -> AccessReport:
    users = Counter(event.user_id for event in events)
    operations = Counter(event.operation for event in events)
    return AccessReport(
        start,
        end,
        len(events),
        tuple(sorted(users.items())),
        tuple((operation, operations[operation]) for operation in OPERATION_ORDER),
    )
