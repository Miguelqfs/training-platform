from fastapi import APIRouter, HTTPException, status

from app.dependencies import Context
from app.facade import FacadeSingletonController
from app.schemas import User, UserCreate
from app.users.domain import DuplicateUserError, UserRegistration

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, context: Context) -> User:
    try:
        user = FacadeSingletonController.get_instance().register_user(
            context,
            UserRegistration(
                username=payload.username,
                email=str(payload.email),
                role=payload.role,
                password=payload.password.get_secret_value(),
            ),
        )
    except DuplicateUserError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        ) from error

    return User(id=user.id, username=user.username, email=user.email, role=user.role)


@router.get("/", response_model=list[User])
def list_users(
    context: Context,
) -> list[User]:
    return [
        User(id=user.id, username=user.username, email=user.email, role=user.role)
        for user in FacadeSingletonController.get_instance().list_users(context)
    ]
