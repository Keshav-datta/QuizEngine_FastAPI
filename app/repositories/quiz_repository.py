from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.quiz import Quiz,QuizStatus


class QuizRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, quiz: Quiz):
        self.db.add(quiz)
        await self.db.flush()
        return quiz

    async def get_by_id(self, quiz_id: int):
        return await self.db.get(Quiz, quiz_id)

    async def get_by_public_id(self, public_id: UUID):
        result = await self.db.execute(
            select(Quiz).where(Quiz.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_published(self):
        result = await self.db.execute(
            select(Quiz)
            .where(Quiz.status == QuizStatus.PUBLISHED)
            .order_by(Quiz.id.desc())
        )
        return result.scalars().all()

    async def delete(self, quiz: Quiz):
        await self.db.delete(quiz)
