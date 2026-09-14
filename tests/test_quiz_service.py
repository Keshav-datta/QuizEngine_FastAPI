from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.exceptions import QuizEmpty, QuizNotDraft, QuizNotFound, QuizNotOwned
from app.models.dto.quizzes import CreateQuizRequest, UpdateQuizRequest
from app.models.enums_models import QuizStatus
from app.services.quiz_service import QuizService


class TestQuizService:
    def setup_method(self):
        self.quiz_repo = Mock()
        self.question_repo = Mock()
        self.quiz_repo.add = AsyncMock()
        self.quiz_repo.get_by_public_id = AsyncMock()
        self.quiz_repo.get_published = AsyncMock()
        self.quiz_repo.delete = AsyncMock()
        self.quiz_repo.db = Mock()
        self.quiz_repo.db.commit = AsyncMock()
        self.quiz_repo.db.refresh = AsyncMock()
        self.question_repo.get_by_quiz = AsyncMock()
        self.service = QuizService(self.quiz_repo, self.question_repo)
        self.quiz_id = uuid4()

    async def test_create_quiz(self):
        self.quiz_repo.add.side_effect = lambda quiz: setattr(quiz, "public_id", self.quiz_id)
        data = CreateQuizRequest(title="Python", description="Basics", duration_minutes=30)
        result = await self.service.create_quiz(data, 2)

        assert result.title == "Python"
        assert result.owner_id == 2
        assert result.status == QuizStatus.DRAFT
        self.quiz_repo.add.assert_awaited_once()
        self.quiz_repo.db.commit.assert_awaited_once()

    async def test_get_quizzes(self):
        quizzes = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        self.quiz_repo.get_published.return_value = quizzes
        assert await self.service.get_quizzes() == quizzes

    async def test_get_quiz_success(self):
        quiz = SimpleNamespace(public_id=self.quiz_id)
        self.quiz_repo.get_by_public_id.return_value = quiz
        assert await self.service.get_quiz(self.quiz_id) is quiz

    async def test_get_quiz_not_found(self):
        self.quiz_repo.get_by_public_id.return_value = None
        with pytest.raises(QuizNotFound):
            await self.service.get_quiz(self.quiz_id)

    async def test_update_quiz_success(self):
        quiz = SimpleNamespace(public_id=self.quiz_id, owner_id=2, status=QuizStatus.DRAFT, title="Old", description="Old", duration_minutes=20)
        self.quiz_repo.get_by_public_id.return_value = quiz
        result = await self.service.update_quiz(self.quiz_id, UpdateQuizRequest(title="New", duration_minutes=40), 2)

        assert result.title == "New"
        assert result.duration_minutes == 40
        self.quiz_repo.db.commit.assert_awaited_once()

    async def test_update_quiz_publish_success(self):
        quiz = SimpleNamespace(public_id=self.quiz_id, owner_id=2, status=QuizStatus.DRAFT, title="Python")
        self.quiz_repo.get_by_public_id.return_value = quiz
        self.question_repo.get_by_quiz.return_value = [SimpleNamespace(id=1)]

        await self.service.update_quiz(self.quiz_id, UpdateQuizRequest(status=QuizStatus.PUBLISHED), 2)
        assert quiz.status == QuizStatus.PUBLISHED
        self.question_repo.get_by_quiz.assert_awaited_once_with(quiz.id)

    async def test_update_quiz_publish_empty(self):
        quiz = SimpleNamespace(public_id=self.quiz_id, owner_id=2, status=QuizStatus.DRAFT)
        self.quiz_repo.get_by_public_id.return_value = quiz
        self.question_repo.get_by_quiz.return_value = []

        with pytest.raises(QuizEmpty):
            await self.service.update_quiz(self.quiz_id, UpdateQuizRequest(status=QuizStatus.PUBLISHED), 2)
        self.quiz_repo.db.commit.assert_not_awaited()

    async def test_update_quiz_not_owned(self):
        self.quiz_repo.get_by_public_id.return_value = SimpleNamespace(public_id=self.quiz_id, owner_id=3, status=QuizStatus.DRAFT)
        with pytest.raises(QuizNotOwned):
            await self.service.update_quiz(self.quiz_id, UpdateQuizRequest(title="New"), 2)

    async def test_update_published_quiz(self):
        self.quiz_repo.get_by_public_id.return_value = SimpleNamespace(public_id=self.quiz_id, owner_id=2, status=QuizStatus.PUBLISHED)
        with pytest.raises(QuizNotDraft):
            await self.service.update_quiz(self.quiz_id, UpdateQuizRequest(title="New"), 2)

    async def test_delete_success(self):
        quiz = SimpleNamespace(public_id=self.quiz_id, owner_id=2, status=QuizStatus.DRAFT)
        self.quiz_repo.get_by_public_id.return_value = quiz
        await self.service.delete_quiz(self.quiz_id, 2)
        self.quiz_repo.delete.assert_awaited_once_with(quiz)
        self.quiz_repo.db.commit.assert_awaited_once()

    async def test_delete_not_owned(self):
        self.quiz_repo.get_by_public_id.return_value = SimpleNamespace(public_id=self.quiz_id, owner_id=3, status=QuizStatus.DRAFT)
        with pytest.raises(QuizNotOwned):
            await self.service.delete_quiz(self.quiz_id, 2)
        self.quiz_repo.delete.assert_not_awaited()

    async def test_delete_published_quiz(self):
        self.quiz_repo.get_by_public_id.return_value = SimpleNamespace(public_id=self.quiz_id, owner_id=2, status=QuizStatus.PUBLISHED)
        with pytest.raises(QuizNotDraft):
            await self.service.delete_quiz(self.quiz_id, 2)
        self.quiz_repo.delete.assert_not_awaited()

    def test_check_owner_success(self):
        QuizService.check_owner(SimpleNamespace(owner_id=2), 2)

    def test_check_owner_failure(self):
        with pytest.raises(QuizNotOwned):
            QuizService.check_owner(SimpleNamespace(owner_id=3), 2)
