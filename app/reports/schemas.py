import re
from typing import Annotated

from pydantic import AwareDatetime, BeforeValidator

RFC3339_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})"
)


def require_rfc3339(value: object) -> object:
    if not isinstance(value, str) or RFC3339_PATTERN.fullmatch(value) is None:
        raise ValueError("Instante deve estar em RFC 3339 com fuso explícito")
    return value


RFC3339Instant = Annotated[AwareDatetime, BeforeValidator(require_rfc3339)]
