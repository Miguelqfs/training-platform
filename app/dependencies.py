from typing import Annotated

from fastapi import Depends, Request

from app.facade import ApplicationContext


def get_context(request: Request) -> ApplicationContext:
    return request.app.state.context


Context = Annotated[ApplicationContext, Depends(get_context)]
