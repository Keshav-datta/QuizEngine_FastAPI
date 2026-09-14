from uuid import UUID

from app.exceptions import QuizNotFound
from app.models.dto.leaderboard import LeaderboardEntry
from app.repositories.leaderboard_repository import LeaderboardRepo
from app.repositories.quiz_repository import QuizRepo


class LeaderboardService:
    def __init__(self, repo: LeaderboardRepo, quiz_repo: QuizRepo):
        self.repo = repo
        self.quiz_repo = quiz_repo

    async def get_leaderboard(self, quiz_public_id: UUID):
        quiz = await self.quiz_repo.get_by_public_id(quiz_public_id)

        if quiz is None:
            raise QuizNotFound("Quiz not found", "QUIZ_NOT_FOUND")

        attempts = await self.repo.get_for_quiz(quiz.id)
        best_scores = {}

        for attempt, user in attempts:
            if user.id not in best_scores:
                best_scores[user.id] = (attempt, user)

        return [
            LeaderboardEntry(
                rank=rank,
                user_id=user.public_id,
                name=user.name,
                score=attempt.score,
                submitted_at=attempt.submitted_at,
            )
            for rank, (attempt, user) in enumerate(best_scores.values(), start=1)
        ]
