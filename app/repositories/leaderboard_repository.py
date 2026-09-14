from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.attempt import QuizAttempt,AttemptStatus
from app.models.db.user import User


class LeaderboardRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_quiz(self, quiz_id: int):
        result = await self.db.execute(
            select(QuizAttempt, User)
            .join(User, User.id == QuizAttempt.user_id)
            .where(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.status == AttemptStatus.COMPLETED,
            )
            .order_by(
                QuizAttempt.score.desc(),
                QuizAttempt.submitted_at.asc(),
            )
        )
        return result.all()
