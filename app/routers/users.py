from fastapi import APIRouter, HTTPException, status

from app.schemas import User, UserCreate

router = APIRouter(prefix="/users", tags=["users"])
users: list[User] = []


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate) -> User:
    if any(user.username == payload.username or user.email == payload.email for user in users):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuário ou e-mail já cadastrado")

    user = User(id=len(users) + 1, **payload.model_dump())
    users.append(user)
    return user


@router.get("/", response_model=list[User])
def list_users() -> list[User]:
    return users
