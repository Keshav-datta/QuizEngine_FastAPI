import uuid
from enum import Enum as modelEnum

from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.db.base import Base


class QuestionType(str, modelEnum):
    MCQ = "MCQ"
    TRUE_FALSE = "TRUE_FALSE"
    SUBJECTIVE = "SUBJECTIVE"


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    type = Column(Enum(QuestionType), nullable=False)
    question_text = Column(Text, nullable=False)
    marks = Column(Float, nullable=False, default=1)
    negative_marks = Column(Float, nullable=False, default=0)
    correct_answer = Column(String(255), nullable=True)

    options = relationship(
        "QuestionOption",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    option_text = Column(String(255), nullable=False)
    is_correct = Column(Boolean, nullable=False, default=False)
