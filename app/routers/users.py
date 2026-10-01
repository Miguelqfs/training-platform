from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.schemas import User, UserCreate
from app.users.domain import DuplicateUserError
from app.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(request: Request) -> UserService:
    return request.app.state.user_service


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate, service: Annotated[UserService, Depends(get_user_service)]
) -> User:
    try:
        user = service.add_user(
            payload.username,
            str(payload.email),
            payload.role,
            payload.password.get_secret_value(),
        )
    except DuplicateUserError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        ) from error

    return User(id=user.id, username=user.username, email=user.email, role=user.role)


@router.get("/", response_model=list[User])
def list_users(
    service: Annotated[UserService, Depends(get_user_service)],
) -> list[User]:
    return [
        User(id=user.id, username=user.username, email=user.email, role=user.role)
        for user in service.list_users()
    ]
