from fastapi import FastAPI

from app.routers.users import router as users_router

app = FastAPI(title="Users API")
app.include_router(users_router)
