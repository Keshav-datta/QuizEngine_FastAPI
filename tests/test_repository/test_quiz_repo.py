from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.models.db.quiz import Quiz
from app.repositories.quiz_repository import QuizRepo


class TestQuizRepo:

    def setup_method(self):
        self.db = Mock()
        self.db.get = AsyncMock()
        self.db.execute = AsyncMock()
        self.db.add = Mock()
        self.db.flush = AsyncMock()
        self.db.delete = AsyncMock()

        self.repo = QuizRepo(self.db)

    async def test_add_quiz(self):
        quiz = Mock(spec=Quiz)

        result = await self.repo.add(quiz)

        self.db.add.assert_called_once_with(quiz)
        self.db.flush.assert_awaited_once()

        assert result == quiz

    async def test_get_by_id_success(self):
        quiz = Mock(spec=Quiz)
        quiz.id = 10

        self.db.get.return_value = quiz

        result = await self.repo.get_by_id(10)

        self.db.get.assert_awaited_once_with(Quiz, 10)

        assert result == quiz

    async def test_get_by_id_not_found(self):
        self.db.get.return_value = None

        result = await self.repo.get_by_id(999)

        self.db.get.assert_awaited_once_with(Quiz, 999)

        assert result is None

    async def test_get_by_public_id_success(self):
        public_id = uuid4()
        quiz = Mock(spec=Quiz)

        result_mock = Mock()
        result_mock.scalar_one_or_none.return_value = quiz

        self.db.execute.return_value = result_mock

        result = await self.repo.get_by_public_id(public_id)

        self.db.execute.assert_awaited_once()
        result_mock.scalar_one_or_none.assert_called_once_with()

        assert result == quiz

    async def test_get_by_public_id_not_found(self):
        public_id = uuid4()

        result_mock = Mock()
        result_mock.scalar_one_or_none.return_value = None

        self.db.execute.return_value = result_mock

        result = await self.repo.get_by_public_id(public_id)

        self.db.execute.assert_awaited_once()

        assert result is None

    async def test_get_published_success(self):
        quiz1 = Mock(spec=Quiz)
        quiz2 = Mock(spec=Quiz)

        result_mock = Mock()
        result_mock.scalars.return_value.all.return_value = [
            quiz1,
            quiz2
        ]

        self.db.execute.return_value = result_mock

        result = await self.repo.get_published()

        self.db.execute.assert_awaited_once()
        result_mock.scalars.assert_called_once_with()
        result_mock.scalars.return_value.all.assert_called_once_with()

        assert result == [quiz1, quiz2]

    async def test_get_published_empty(self):
        result_mock = Mock()
        result_mock.scalars.return_value.all.return_value = []

        self.db.execute.return_value = result_mock

        result = await self.repo.get_published()

        assert result == []

    async def test_delete_quiz(self):
        quiz = Mock(spec=Quiz)

        await self.repo.delete(quiz)

        self.db.delete.assert_awaited_once_with(quiz)