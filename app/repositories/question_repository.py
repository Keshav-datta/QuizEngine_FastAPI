from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.question import Question, QuestionOption


class QuestionRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, question: Question):
        self.db.add(question)
        await self.db.flush()
        return question

    async def get_by_public_id(self, public_id: UUID):
        result = await self.db.execute(
            select(Question).where(Question.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_option_by_public_id(self, public_id: UUID):
        result = await self.db.execute(
            select(QuestionOption).where(QuestionOption.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_by_quiz(self, quiz_id: int):
        result = await self.db.execute(
            select(Question)
            .where(Question.quiz_id == quiz_id)
            .order_by(Question.id)
        )
        return result.scalars().all()

    async def delete(self, question: Question):
        await self.db.delete(question)
