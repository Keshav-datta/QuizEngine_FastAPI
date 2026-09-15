from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.db.quiz import QuizStatus


class CreateQuizRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    duration_minutes: int = Field(gt=0, le=1440)


class UpdateQuizRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    duration_minutes: int | None = Field(default=None, gt=0, le=1440)
    status: QuizStatus | None = None


class QuizResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    title: str
    description: str | None
    duration_minutes: int
    status: QuizStatus
