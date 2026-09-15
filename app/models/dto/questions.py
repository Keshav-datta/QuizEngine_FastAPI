from uuid import UUID

from pydantic import BaseModel, Field

from app.models.db.question import QuestionType


class OptionRequest(BaseModel):
    option_text: str = Field(min_length=1, max_length=255)
    is_correct: bool = False


class CreateQuestionRequest(BaseModel):
    type: QuestionType
    question_text: str = Field(min_length=1)
    marks: float = Field(gt=0)
    negative_marks: float = Field(ge=0)
    correct_answer: str | None = Field(default=None, max_length=255)
    options: list[OptionRequest] = Field(default_factory=list)


class OptionResponse(BaseModel):
    public_id: UUID
    option_text: str


class QuestionResponse(BaseModel):
    public_id: UUID
    type: QuestionType
    question_text: str
    marks: float
    negative_marks: float
    options: list[OptionResponse]
