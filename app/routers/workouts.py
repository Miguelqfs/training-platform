from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Path, Response, status

from app.dependencies import Context
from app.facade import FacadeSingletonController
from app.schemas import ErrorMessage, ValidationErrorResponse
from app.users.domain import PersistenceError
from app.workouts.domain import WorkoutRegistration, WorkoutUpdate
from app.workouts.schemas import WorkoutCreate, WorkoutResponse, WorkoutUpdatePayload

router = APIRouter(
    prefix="/workouts",
    tags=["workouts"],
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorMessage,
            "description": PersistenceError.WORKOUT_MESSAGE,
        }
    },
)
WORKOUT_INPUT_ERRORS = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorMessage,
        "description": "Registro não encontrado",
    },
    HTTPStatus.UNPROCESSABLE_ENTITY: {
        "model": ValidationErrorResponse,
        "description": "Entrada inválida",
    },
}
WorkoutId = Annotated[int, Path(gt=0)]


@router.post(
    "/",
    response_model=WorkoutResponse,
    status_code=status.HTTP_201_CREATED,
    responses=WORKOUT_INPUT_ERRORS,
)
def create_workout(payload: WorkoutCreate, context: Context) -> WorkoutResponse:
    workout = FacadeSingletonController.get_instance().create_workout(
        context, WorkoutRegistration(payload.user_id, payload.name, payload.description)
    )
    return WorkoutResponse.model_validate(workout)


@router.get("/", response_model=list[WorkoutResponse])
def list_workouts(context: Context) -> list[WorkoutResponse]:
    return [
        WorkoutResponse.model_validate(workout)
        for workout in FacadeSingletonController.get_instance().list_workouts(context)
    ]


@router.get(
    "/{workout_id}", response_model=WorkoutResponse, responses=WORKOUT_INPUT_ERRORS
)
def get_workout(workout_id: WorkoutId, context: Context) -> WorkoutResponse:
    return WorkoutResponse.model_validate(
        FacadeSingletonController.get_instance().get_workout(context, workout_id)
    )


@router.put(
    "/{workout_id}", response_model=WorkoutResponse, responses=WORKOUT_INPUT_ERRORS
)
def update_workout(
    workout_id: WorkoutId, payload: WorkoutUpdatePayload, context: Context
) -> WorkoutResponse:
    workout = FacadeSingletonController.get_instance().update_workout(
        context, workout_id, WorkoutUpdate(payload.name, payload.description)
    )
    return WorkoutResponse.model_validate(workout)


@router.delete(
    "/{workout_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=WORKOUT_INPUT_ERRORS,
)
def delete_workout(workout_id: WorkoutId, context: Context) -> Response:
    FacadeSingletonController.get_instance().delete_workout(context, workout_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
