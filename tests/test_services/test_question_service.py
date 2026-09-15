from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.exceptions import QuizEmpty, QuizNotDraft, QuizNotFound, QuizNotOwned
from app.models.enums_models import QuizStatus
from app.services.quiz_service import QuizService


class TestQuizService:

    def setup_method(self):
        self.quiz_repo = Mock()
        self.question_repo = Mock()

        self.quiz_repo.get_published = AsyncMock()
        self.quiz_repo.get_by_public_id = AsyncMock()
        self.quiz_repo.add = AsyncMock()
        self.quiz_repo.delete = AsyncMock()

        self.question_repo.get_by_quiz = AsyncMock()

        self.quiz_repo.db = Mock()
        self.quiz_repo.db.commit = AsyncMock()
        self.quiz_repo.db.refresh = AsyncMock()

        self.service = QuizService(
            self.quiz_repo,
            self.question_repo
        )

    async def test_create_quiz(self):
        data = Mock()
        data.title = "Python Quiz"
        data.description = "Python fundamentals"
        data.duration_minutes = 30

        user_id = 1

        quiz = await self.service.create_quiz(data, user_id)

        self.quiz_repo.add.assert_awaited_once_with(quiz)
        self.quiz_repo.db.commit.assert_awaited_once()
        self.quiz_repo.db.refresh.assert_awaited_once_with(quiz)

        assert quiz.title == "Python Quiz"
        assert quiz.description == "Python fundamentals"
        assert quiz.duration_minutes == 30
        assert quiz.owner_id == user_id

    async def test_get_quizzes(self):
        quizzes = [Mock(), Mock()]
        self.quiz_repo.get_published.return_value = quizzes

        result = await self.service.get_quizzes()

        self.quiz_repo.get_published.assert_awaited_once_with()
        assert result == quizzes

    async def test_get_quiz_success(self):
        quiz_id = uuid4()
        quiz = Mock()

        self.quiz_repo.get_by_public_id.return_value = quiz

        result = await self.service.get_quiz(quiz_id)

        self.quiz_repo.get_by_public_id.assert_awaited_once_with(
            quiz_id
        )
        assert result == quiz

    async def test_get_quiz_not_found(self):
        quiz_id = uuid4()

        self.quiz_repo.get_by_public_id.return_value = None

        with pytest.raises(QuizNotFound):
            await self.service.get_quiz(quiz_id)

    async def test_update_quiz_success(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.owner_id = 1
        quiz.status = QuizStatus.DRAFT

        self.quiz_repo.get_by_public_id.return_value = quiz

        data = Mock()
        data.model_dump.return_value = {
            "title": "Updated Quiz",
            "description": "Updated description"
        }

        result = await self.service.update_quiz(
            quiz_id,
            data,
            1
        )

        self.quiz_repo.db.commit.assert_awaited_once()
        self.quiz_repo.db.refresh.assert_awaited_once_with(quiz)

        assert result == quiz
        assert quiz.title == "Updated Quiz"
        assert quiz.description == "Updated description"

    async def test_update_quiz_not_owner(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.owner_id = 2
        quiz.status = QuizStatus.DRAFT

        self.quiz_repo.get_by_public_id.return_value = quiz

        data = Mock()

        with pytest.raises(QuizNotOwned):
            await self.service.update_quiz(
                quiz_id,
                data,
                1
            )

        self.quiz_repo.db.commit.assert_not_awaited()

    async def test_update_published_quiz(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.owner_id = 1
        quiz.status = QuizStatus.PUBLISHED

        self.quiz_repo.get_by_public_id.return_value = quiz

        data = Mock()

        with pytest.raises(QuizNotDraft):
            await self.service.update_quiz(
                quiz_id,
                data,
                1
            )

    async def test_publish_quiz_success(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.id = 10
        quiz.owner_id = 1
        quiz.status = QuizStatus.DRAFT

        self.quiz_repo.get_by_public_id.return_value = quiz
        self.question_repo.get_by_quiz.return_value = [Mock()]

        data = Mock()
        data.model_dump.return_value = {
            "status": QuizStatus.PUBLISHED
        }

        result = await self.service.update_quiz(
            quiz_id,
            data,
            1
        )

        self.question_repo.get_by_quiz.assert_awaited_once_with(10)

        assert result == quiz
        assert quiz.status == QuizStatus.PUBLISHED

    async def test_publish_empty_quiz(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.id = 10
        quiz.owner_id = 1
        quiz.status = QuizStatus.DRAFT

        self.quiz_repo.get_by_public_id.return_value = quiz
        self.question_repo.get_by_quiz.return_value = []

        data = Mock()
        data.model_dump.return_value = {
            "status": QuizStatus.PUBLISHED
        }

        with pytest.raises(QuizEmpty):
            await self.service.update_quiz(
                quiz_id,
                data,
                1
            )

        self.quiz_repo.db.commit.assert_not_awaited()

    async def test_delete_quiz_success(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.owner_id = 1
        quiz.status = QuizStatus.DRAFT

        self.quiz_repo.get_by_public_id.return_value = quiz

        await self.service.delete_quiz(
            quiz_id,
            1
        )

        self.quiz_repo.delete.assert_awaited_once_with(quiz)
        self.quiz_repo.db.commit.assert_awaited_once()

    async def test_delete_quiz_not_owner(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.owner_id = 2
        quiz.status = QuizStatus.DRAFT

        self.quiz_repo.get_by_public_id.return_value = quiz

        with pytest.raises(QuizNotOwned):
            await self.service.delete_quiz(
                quiz_id,
                1
            )

        self.quiz_repo.delete.assert_not_awaited()

    async def test_delete_published_quiz(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.owner_id = 1
        quiz.status = QuizStatus.PUBLISHED

        self.quiz_repo.get_by_public_id.return_value = quiz

        with pytest.raises(QuizNotDraft):
            await self.service.delete_quiz(
                quiz_id,
                1
            )

        self.quiz_repo.delete.assert_not_awaited()

    def test_check_owner_success(self):
        quiz = Mock()
        quiz.owner_id = 1

        QuizService.check_owner(quiz, 1)

    def test_check_owner_failure(self):
        quiz = Mock()
        quiz.owner_id = 2

        with pytest.raises(QuizNotOwned):
            QuizService.check_owner(quiz, 1)