from fastapi import APIRouter, status

from app.dependencies import Context
from app.facade import FacadeSingletonController
from app.schemas import ErrorMessage
from app.workouts.schemas import EntityCount

router = APIRouter(
    prefix="/statistics",
    tags=["statistics"],
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorMessage,
            "description": "Armazenamento de usuários ou treinos indisponível",
        }
    },
)


@router.get("/entities", response_model=EntityCount)
def count_entities(context: Context) -> EntityCount:
    return EntityCount(
        total=FacadeSingletonController.get_instance().count_entities(context)
    )
