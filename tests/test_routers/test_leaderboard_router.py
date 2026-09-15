from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.routers.leaderboard import get_leaderboard


class TestGetLeaderboard:

    def setup_method(self):
        self.service = Mock()
        self.service.get_leaderboard = AsyncMock()

        self.user = Mock()
        self.user.id = 1

        self.quiz_id = uuid4()

    async def test_get_leaderboard_success(self):
        entries = [
            {
                "rank": 1,
                "user_id": uuid4(),
                "score": 10
            },
            {
                "rank": 2,
                "user_id": uuid4(),
                "score": 8
            }
        ]

        self.service.get_leaderboard.return_value = entries

        response = await get_leaderboard(
            self.quiz_id,
            self.user,
            self.service
        )

        self.service.get_leaderboard.assert_awaited_once_with(
            self.quiz_id
        )

        assert response.success is True
        assert response.message == "Leaderboard fetched successfully"
        assert response.data == entries

    async def test_get_leaderboard_service_exception(self):
        self.service.get_leaderboard.side_effect = Exception(
            "Quiz not found"
        )

        with pytest.raises(Exception, match="Quiz not found"):
            await get_leaderboard(
                self.quiz_id,
                self.user,
                self.service
            )