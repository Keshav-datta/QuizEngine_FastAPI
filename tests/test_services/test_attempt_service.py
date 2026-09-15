from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.exceptions import QuizNotFound
from app.services.leaderboard_service import LeaderboardService


class TestLeaderboardService:

    def setup_method(self):
        self.repo = Mock()
        self.quiz_repo = Mock()

        self.repo.get_for_quiz = AsyncMock()
        self.quiz_repo.get_by_public_id = AsyncMock()

        self.service = LeaderboardService(
            self.repo,
            self.quiz_repo
        )

    async def test_get_leaderboard_success(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.id = 10

        user1 = Mock()
        user1.id = 1
        user1.public_id = uuid4()
        user1.name = "Keshav"

        user2 = Mock()
        user2.id = 2
        user2.public_id = uuid4()
        user2.name = "Akshat"

        attempt1 = Mock()
        attempt1.score = 10
        attempt1.submitted_at = Mock()

        attempt2 = Mock()
        attempt2.score = 8
        attempt2.submitted_at = Mock()

        self.quiz_repo.get_by_public_id.return_value = quiz
        self.repo.get_for_quiz.return_value = [
            (attempt1, user1),
            (attempt2, user2)
        ]

        result = await self.service.get_leaderboard(quiz_id)

        self.quiz_repo.get_by_public_id.assert_awaited_once_with(
            quiz_id
        )
        self.repo.get_for_quiz.assert_awaited_once_with(10)

        assert len(result) == 2

        assert result[0].rank == 1
        assert result[0].user_id == user1.public_id
        assert result[0].name == "Keshav"
        assert result[0].score == 10

        assert result[1].rank == 2
        assert result[1].user_id == user2.public_id
        assert result[1].name == "Akshat"
        assert result[1].score == 8

    async def test_get_leaderboard_keeps_best_score_per_user(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.id = 10

        user = Mock()
        user.id = 1
        user.public_id = uuid4()
        user.name = "Keshav"

        first_attempt = Mock()
        first_attempt.score = 10
        first_attempt.submitted_at = Mock()

        second_attempt = Mock()
        second_attempt.score = 8
        second_attempt.submitted_at = Mock()

        self.quiz_repo.get_by_public_id.return_value = quiz
        self.repo.get_for_quiz.return_value = [
            (first_attempt, user),
            (second_attempt, user)
        ]

        result = await self.service.get_leaderboard(quiz_id)

        assert len(result) == 1
        assert result[0].score == 10
        assert result[0].user_id == user.public_id

    async def test_get_leaderboard_quiz_not_found(self):
        quiz_id = uuid4()

        self.quiz_repo.get_by_public_id.return_value = None

        with pytest.raises(QuizNotFound):
            await self.service.get_leaderboard(quiz_id)

        self.repo.get_for_quiz.assert_not_awaited()

    async def test_get_leaderboard_empty(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.id = 10

        self.quiz_repo.get_by_public_id.return_value = quiz
        self.repo.get_for_quiz.return_value = []

        result = await self.service.get_leaderboard(quiz_id)

        assert result == []