from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums_models import AttemptStatus


class SubmitAnswerRequest(BaseModel):
    question_id: UUID
    answer: str = Field(min_length=1, max_length=255)


class AttemptResponse(BaseModel):
    public_id: UUID
    quiz_id: UUID
    started_at: datetime
    expires_at: datetime
    score: float
    status: AttemptStatus


class AttemptResult(AttemptResponse):
    submitted_at: datetime | None


class ScoreResponse(BaseModel):
    attempt_id: UUID
    score: float
    status: AttemptStatus


class ReviewItem(BaseModel):
    question_id: UUID
    question_text: str
    submitted_answer: str | None
    correct_answer: str | None
    is_correct: bool
    marks_awarded: float
    is_skipped: bool
    status: str


class ReviewResponse(BaseModel):
    attempt_id: UUID
    quiz_id: UUID
    score: float
    status: AttemptStatus
    total_questions: int
    correct_answers: int
    wrong_answers: int
    items: list[ReviewItem]
