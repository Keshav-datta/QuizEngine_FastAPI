import uuid
from datetime import datetime
from enum import Enum as modelEnum

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint,Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.db.base import Base


class AttemptStatus(str, modelEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime(), nullable=False)
    expires_at = Column(DateTime(), nullable=False)
    submitted_at = Column(DateTime(), nullable=True)
    score = Column(Float, nullable=False, default=0)
    status = Column(Enum(AttemptStatus), nullable=False, default=AttemptStatus.IN_PROGRESS)


class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),)

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_option_id = Column(Integer, ForeignKey("question_options.id"), nullable=True)
    answer_text = Column(String(255), nullable=True)
    is_correct = Column(Boolean, nullable=False, default=False)
    marks_awarded = Column(Float, nullable=False, default=0)
    is_skipped = Column(Boolean, nullable=False, default=False)

    question = relationship("Question", lazy="joined")
    selected_option = relationship("QuestionOption", lazy="joined")


