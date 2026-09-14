import uuid
from enum import Enum as modelEnum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.db.base import Base


class QuizStatus(str, modelEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(Enum(QuizStatus), nullable=False, default=QuizStatus.DRAFT)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    questions = relationship("Question", cascade="all, delete-orphan")


