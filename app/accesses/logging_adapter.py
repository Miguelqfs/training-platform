import logging

from app.accesses.domain import AccessEvent


class LoggingAccessLogAdapter:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = (
            logger if logger is not None else logging.getLogger("app.accesses")
        )

    def record(self, event: AccessEvent) -> None:
        self._logger.info(
            "user_id=%s operation=%s occurred_at=%s",
            event.user_id,
            event.operation,
            event.occurred_at.isoformat(),
        )
