from datetime import datetime
from typing import Protocol

from app.accesses.domain import AccessEvent


class AccessEventRepository(Protocol):
    def add(self, event: AccessEvent) -> None: ...
    def list_between(self, start: datetime, end: datetime) -> list[AccessEvent]: ...


class AccessLogPort(Protocol):
    def record(self, event: AccessEvent) -> None: ...
