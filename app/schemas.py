from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr


class User(UserCreate):
    id: int
