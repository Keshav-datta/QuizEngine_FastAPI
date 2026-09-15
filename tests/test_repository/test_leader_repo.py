from unittest.mock import AsyncMock, Mock

from app.repositories.leaderboard_repository import LeaderboardRepo


class TestLeaderboardRepo:

    def setup_method(self):
        self.db = Mock()
        self.db.execute = AsyncMock()

        self.repo = LeaderboardRepo(self.db)

    async def test_get_for_quiz_success(self):
        user1 = Mock()
        user2 = Mock()

        attempt1 = Mock()
        attempt1.score = 10

        attempt2 = Mock()
        attempt2.score = 8

        rows = [
            (attempt1, user1),
            (attempt2, user2)
        ]

        result_mock = Mock()
        result_mock.all.return_value = rows

        self.db.execute.return_value = result_mock

        result = await self.repo.get_for_quiz(10)

        self.db.execute.assert_awaited_once()
        result_mock.all.assert_called_once_with()

        assert result == rows

    async def test_get_for_quiz_empty(self):
        result_mock = Mock()
        result_mock.all.return_value = []

        self.db.execute.return_value = result_mock

        result = await self.repo.get_for_quiz(10)

        self.db.execute.assert_awaited_once()

        assert result == []