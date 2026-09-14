from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.attempt import Answer, QuizAttempt,AttemptStatus


class AttemptRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, attempt: QuizAttempt):
        self.db.add(attempt)
        await self.db.flush()
        return attempt

    async def get_by_public_id(self, public_id: UUID):
        result = await self.db.execute(
            select(QuizAttempt).where(QuizAttempt.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_active(self, quiz_id: int, user_id: int):
        result = await self.db.execute(
            select(QuizAttempt).where(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.user_id == user_id,
                QuizAttempt.status == AttemptStatus.IN_PROGRESS,
            )
        )
        return result.scalar_one_or_none()

    async def get_answer(self, attempt_id: int, question_id: int):
        result = await self.db.execute(
            select(Answer).where(
                Answer.attempt_id == attempt_id,
                Answer.question_id == question_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_answer(self, answer: Answer):
        self.db.add(answer)
        await self.db.flush()
        return answer

    async def get_answers(self, attempt_id: int):
        result = await self.db.execute(
            select(Answer)
            .where(Answer.attempt_id == attempt_id)
            .order_by(Answer.question_id)
        )
        return result.scalars().all()
