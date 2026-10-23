from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator

from app.workouts.policy import (
    MAX_WORKOUT_DESCRIPTION_LENGTH,
    MAX_WORKOUT_NAME_LENGTH,
    MIN_WORKOUT_NAME_LENGTH,
)


class WorkoutUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: StrictStr = Field(
        min_length=MIN_WORKOUT_NAME_LENGTH, max_length=MAX_WORKOUT_NAME_LENGTH
    )
    description: StrictStr = Field(
        default="", max_length=MAX_WORKOUT_DESCRIPTION_LENGTH
    )

    @field_validator("name", "description", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class WorkoutCreate(WorkoutUpdatePayload):
    user_id: Annotated[StrictInt, Field(gt=0)]


class WorkoutResponse(WorkoutCreate):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: int = Field(gt=0)


class EntityCount(BaseModel):
    total: int = Field(ge=0)
