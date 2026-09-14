from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.exceptions import QuizNotFound
from app.services.leaderboard_service import LeaderboardService


class TestLeaderboardService:
    def setup_method(self):
        self.repo = Mock(); self.quiz_repo = Mock(); self.repo.get_for_quiz = AsyncMock(); self.quiz_repo.get_by_public_id = AsyncMock(); self.service = LeaderboardService(self.repo, self.quiz_repo); self.quiz_id = uuid4()

    async def test_best_score_once_per_user(self):
        user1 = SimpleNamespace(id=1, public_id=uuid4(), name="Akshat"); user2 = SimpleNamespace(id=2, public_id=uuid4(), name="Aryan")
        self.quiz_repo.get_by_public_id.return_value = SimpleNamespace(id=10)
        self.repo.get_for_quiz.return_value = [(SimpleNamespace(score=9, submitted_at="a"), user1), (SimpleNamespace(score=8, submitted_at="b"), user2), (SimpleNamespace(score=7, submitted_at="c"), user1)]
        result = await self.service.get_leaderboard(self.quiz_id)
        assert len(result) == 2; assert result[0].name == "Akshat"; assert result[0].score == 9; assert result[0].rank == 1; assert result[1].rank == 2

    async def test_quiz_not_found(self):
        self.quiz_repo.get_by_public_id.return_value = None
        with pytest.raises(QuizNotFound): await self.service.get_leaderboard(self.quiz_id)
        self.repo.get_for_quiz.assert_not_awaited()

    async def test_empty_leaderboard(self):
        self.quiz_repo.get_by_public_id.return_value = SimpleNamespace(id=10); self.repo.get_for_quiz.return_value = []
        assert await self.service.get_leaderboard(self.quiz_id) == []
