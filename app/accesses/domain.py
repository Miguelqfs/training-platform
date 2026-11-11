from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Operation = Literal["create", "get", "update", "delete"]


@dataclass(frozen=True)
class AccessEvent:
    user_id: int
    operation: Operation
    occurred_at: datetime
