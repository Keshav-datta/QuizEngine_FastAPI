from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.models.dto.quizzes import CreateQuizRequest, UpdateQuizRequest, QuizResponse
from app.routers.quiz import (
    create_quiz,
    get_quizzes,
    get_quiz,
    update_quiz,
    delete_quiz,
)


class TestCreateQuiz:

    def setup_method(self):
        self.service = Mock()
        self.service.create_quiz = AsyncMock()

        self.user = Mock()
        self.user.id = 1

        self.data = CreateQuizRequest(
            title="Python Quiz",
            description="Python fundamentals",
            duration_minutes=30
        )

    async def test_create_quiz_success(self):
        quiz = Mock()
        quiz.public_id = uuid4()
        quiz.title = "Python Quiz"
        quiz.description = "Python fundamentals"
        quiz.duration_minutes = 30
        quiz.status = Mock()
        quiz.status.value = "DRAFT"

        self.service.create_quiz.return_value = quiz

        response = await create_quiz(
            self.data,
            self.user,
            self.service
        )

        self.service.create_quiz.assert_awaited_once_with(
            self.data,
            self.user.id
        )

        assert response.success is True
        assert response.message == "Quiz created successfully"
        assert isinstance(response.data, QuizResponse)
        assert response.data.public_id == quiz.public_id
        assert response.data.title == quiz.title
        assert response.data.description == quiz.description
        assert response.data.duration_minutes == quiz.duration_minutes
        assert response.data.status.value == "DRAFT"

    async def test_create_quiz_service_exception(self):
        self.service.create_quiz.side_effect = Exception("Creation failed")

        with pytest.raises(Exception, match="Creation failed"):
            await create_quiz(
                self.data,
                self.user,
                self.service
            )


class TestGetQuizzes:

    def setup_method(self):
        self.service = Mock()
        self.service.get_quizzes = AsyncMock()

        self.user = Mock()

    async def test_get_quizzes_success(self):
        quiz1 = Mock()
        quiz1.public_id = uuid4()
        quiz1.title = "Python"
        quiz1.description = "Python quiz"
        quiz1.duration_minutes = 30
        quiz1.status = Mock()
        quiz1.status.value = "PUBLISHED"

        quiz2 = Mock()
        quiz2.public_id = uuid4()
        quiz2.title = "FastAPI"
        quiz2.description = "FastAPI quiz"
        quiz2.duration_minutes = 45
        quiz2.status = Mock()
        quiz2.status.value = "PUBLISHED"

        self.service.get_quizzes.return_value = [quiz1, quiz2]

        response = await get_quizzes(
            self.service,
            self.user
        )

        self.service.get_quizzes.assert_awaited_once_with()

        assert response.success is True
        assert response.message == "Quizzes fetched successfully"
        assert len(response.data) == 2

        assert response.data[0].public_id == quiz1.public_id
        assert response.data[0].title == quiz1.title

        assert response.data[1].public_id == quiz2.public_id
        assert response.data[1].title == quiz2.title


class TestGetQuiz:

    def setup_method(self):
        self.service = Mock()
        self.service.get_quiz = AsyncMock()

        self.user = Mock()
        self.quiz_id = uuid4()

    async def test_get_quiz_success(self):
        quiz = Mock()
        quiz.public_id = self.quiz_id
        quiz.title = "Python Quiz"
        quiz.description = "Python fundamentals"
        quiz.duration_minutes = 30
        quiz.status = Mock()
        quiz.status.value = "PUBLISHED"

        self.service.get_quiz.return_value = quiz

        response = await get_quiz(
            self.quiz_id,
            self.service,
            self.user
        )

        self.service.get_quiz.assert_awaited_once_with(self.quiz_id)

        assert response.success is True
        assert response.message == "Quiz fetched successfully"
        assert isinstance(response.data, QuizResponse)
        assert response.data.public_id == self.quiz_id
        assert response.data.title == "Python Quiz"


class TestUpdateQuiz:

    def setup_method(self):
        self.service = Mock()
        self.service.update_quiz = AsyncMock()

        self.user = Mock()
        self.user.id = 1

        self.quiz_id = uuid4()

        self.data = UpdateQuizRequest(
            title="Updated Python Quiz",
            description="Updated description",
            duration_minutes=60
        )

    async def test_update_quiz_success(self):
        quiz = Mock()
        quiz.public_id = self.quiz_id
        quiz.title = "Updated Python Quiz"
        quiz.description = "Updated description"
        quiz.duration_minutes = 60
        quiz.status = Mock()
        quiz.status.value = "DRAFT"

        self.service.update_quiz.return_value = quiz

        response = await update_quiz(
            self.quiz_id,
            self.data,
            self.user,
            self.service
        )

        self.service.update_quiz.assert_awaited_once_with(
            self.quiz_id,
            self.data,
            self.user.id
        )

        assert response.success is True
        assert response.message == "Quiz updated successfully"
        assert response.data.title == "Updated Python Quiz"
        assert response.data.duration_minutes == 60


class TestDeleteQuiz:

    def setup_method(self):
        self.service = Mock()
        self.service.delete_quiz = AsyncMock()

        self.user = Mock()
        self.user.id = 1

        self.quiz_id = uuid4()

    async def test_delete_quiz_success(self):
        self.service.delete_quiz.return_value = None

        response = await delete_quiz(
            self.quiz_id,
            self.user,
            self.service
        )

        self.service.delete_quiz.assert_awaited_once_with(
            self.quiz_id,
            self.user.id
        )

        assert response.success is True
        assert response.message == "Quiz deleted successfully"
        assert response.data is None