from fastapi import FastAPI

from app.routers.users import router as users_router
from app.users.service import UserService


def create_app() -> FastAPI:
    app = FastAPI(title="Users API")
    app.state.user_service = UserService()
    app.include_router(users_router)
    return app


app = create_app()
