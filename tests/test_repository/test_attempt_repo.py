from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.models.db.attempt import Answer, QuizAttempt
from app.repositories.attempt_repository import AttemptRepo


class TestAttemptRepo:

    def setup_method(self):
        self.db = Mock()
        self.db.execute = AsyncMock()
        self.db.add = Mock()
        self.db.flush = AsyncMock()

        self.repo = AttemptRepo(self.db)

    async def test_add_attempt(self):
        attempt = Mock(spec=QuizAttempt)

        result = await self.repo.add(attempt)

        self.db.add.assert_called_once_with(attempt)
        self.db.flush.assert_awaited_once()

        assert result == attempt

    async def test_get_by_public_id_success(self):
        public_id = uuid4()
        attempt = Mock(spec=QuizAttempt)

        result_mock = Mock()
        result_mock.scalar_one_or_none.return_value = attempt

        self.db.execute.return_value = result_mock

        result = await self.repo.get_by_public_id(public_id)

        self.db.execute.assert_awaited_once()
        result_mock.scalar_one_or_none.assert_called_once_with()

        assert result == attempt

    async def test_get_by_public_id_not_found(self):
        public_id = uuid4()

        result_mock = Mock()
        result_mock.scalar_one_or_none.return_value = None

        self.db.execute.return_value = result_mock

        result = await self.repo.get_by_public_id(public_id)

        assert result is None

    async def test_get_active_success(self):
        attempt = Mock(spec=QuizAttempt)

        result_mock = Mock()
        result_mock.scalar_one_or_none.return_value = attempt

        self.db.execute.return_value = result_mock

        result = await self.repo.get_active(
            quiz_id=10,
            user_id=1
        )

        self.db.execute.assert_awaited_once()
        result_mock.scalar_one_or_none.assert_called_once_with()

        assert result == attempt

    async def test_get_active_not_found(self):
        result_mock = Mock()
        result_mock.scalar_one_or_none.return_value = None

        self.db.execute.return_value = result_mock

        result = await self.repo.get_active(
            quiz_id=10,
            user_id=1
        )

        assert result is None

    async def test_get_answer_success(self):
        answer = Mock(spec=Answer)

        result_mock = Mock()
        result_mock.scalar_one_or_none.return_value = answer

        self.db.execute.return_value = result_mock

        result = await self.repo.get_answer(
            attempt_id=100,
            question_id=20
        )

        self.db.execute.assert_awaited_once()
        result_mock.scalar_one_or_none.assert_called_once_with()

        assert result == answer

    async def test_get_answer_not_found(self):
        result_mock = Mock()
        result_mock.scalar_one_or_none.return_value = None

        self.db.execute.return_value = result_mock

        result = await self.repo.get_answer(
            attempt_id=100,
            question_id=20
        )

        assert result is None

    async def test_add_answer(self):
        answer = Mock(spec=Answer)

        result = await self.repo.add_answer(answer)

        self.db.add.assert_called_once_with(answer)
        self.db.flush.assert_awaited_once()

        assert result == answer

    async def test_get_answers_success(self):
        answer1 = Mock(spec=Answer)
        answer2 = Mock(spec=Answer)

        result_mock = Mock()
        result_mock.scalars.return_value.all.return_value = [
            answer1,
            answer2
        ]

        self.db.execute.return_value = result_mock

        result = await self.repo.get_answers(
            attempt_id=100
        )

        self.db.execute.assert_awaited_once()
        result_mock.scalars.assert_called_once_with()
        result_mock.scalars.return_value.all.assert_called_once_with()

        assert result == [answer1, answer2]

    async def test_get_answers_empty(self):
        result_mock = Mock()
        result_mock.scalars.return_value.all.return_value = []

        self.db.execute.return_value = result_mock

        result = await self.repo.get_answers(
            attempt_id=100
        )

        assert result == []