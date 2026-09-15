from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.models.dto.attempts import SubmitAnswerRequest
from app.routers.attempt import (
    start_quiz,
    submit_answer,
    skip_question,
    submit_quiz,
    get_score,
    get_review,
)


class TestStartQuiz:

    def setup_method(self):
        self.service = Mock()
        self.service.start_quiz = AsyncMock()

        self.user = Mock()
        self.user.id = 1

        self.quiz_id = uuid4()

    async def test_start_quiz_success(self):
        attempt = Mock()
        self.service.start_quiz.return_value = attempt

        response = await start_quiz(
            self.quiz_id,
            self.user,
            self.service
        )

        self.service.start_quiz.assert_awaited_once_with(
            self.quiz_id,
            self.user.id
        )

        assert response.success is True
        assert response.message == "Quiz attempt started successfully"
        assert response.data == attempt

    async def test_start_quiz_service_exception(self):
        self.service.start_quiz.side_effect = Exception("Quiz not available")

        with pytest.raises(Exception, match="Quiz not available"):
            await start_quiz(
                self.quiz_id,
                self.user,
                self.service
            )


class TestSubmitAnswer:

    def setup_method(self):
        self.service = Mock()
        self.service.submit_answer = AsyncMock()

        self.user = Mock()
        self.user.id = 1

        self.attempt_id = uuid4()

        self.data = SubmitAnswerRequest(
            question_id=uuid4(),
            answer="Python"
        )

    async def test_submit_answer_success(self):
        attempt = Mock()
        self.service.submit_answer.return_value = attempt

        response = await submit_answer(
            self.attempt_id,
            self.data,
            self.user,
            self.service
        )

        self.service.submit_answer.assert_awaited_once_with(
            self.attempt_id,
            self.data,
            self.user.id
        )

        assert response.success is True
        assert response.message == "Answer submitted successfully"
        assert response.data == attempt

    async def test_submit_answer_service_exception(self):
        self.service.submit_answer.side_effect = Exception("Invalid answer")

        with pytest.raises(Exception, match="Invalid answer"):
            await submit_answer(
                self.attempt_id,
                self.data,
                self.user,
                self.service
            )


class TestSkipQuestion:

    def setup_method(self):
        self.service = Mock()
        self.service.skip_question = AsyncMock()

        self.user = Mock()
        self.user.id = 1

        self.attempt_id = uuid4()
        self.question_id = uuid4()

    async def test_skip_question_success(self):
        attempt = Mock()
        self.service.skip_question.return_value = attempt

        response = await skip_question(
            self.attempt_id,
            self.question_id,
            self.user,
            self.service
        )

        self.service.skip_question.assert_awaited_once_with(
            self.attempt_id,
            self.question_id,
            self.user.id
        )

        assert response.success is True
        assert response.message == "Question skipped successfully"
        assert response.data == attempt

    async def test_skip_question_service_exception(self):
        self.service.skip_question.side_effect = Exception("Question not found")

        with pytest.raises(Exception, match="Question not found"):
            await skip_question(
                self.attempt_id,
                self.question_id,
                self.user,
                self.service
            )


class TestSubmitQuiz:

    def setup_method(self):
        self.service = Mock()
        self.service.finalize_attempt = AsyncMock()

        self.user = Mock()
        self.user.id = 1

        self.attempt_id = uuid4()

    async def test_submit_quiz_success(self):
        result = Mock()
        self.service.finalize_attempt.return_value = result

        response = await submit_quiz(
            self.attempt_id,
            self.user,
            self.service
        )

        self.service.finalize_attempt.assert_awaited_once_with(
            self.attempt_id,
            self.user.id
        )

        assert response.success is True
        assert response.message == "Quiz submitted successfully"
        assert response.data == result

    async def test_submit_quiz_service_exception(self):
        self.service.finalize_attempt.side_effect = Exception("Attempt expired")

        with pytest.raises(Exception, match="Attempt expired"):
            await submit_quiz(
                self.attempt_id,
                self.user,
                self.service
            )


class TestGetScore:

    def setup_method(self):
        self.service = Mock()
        self.service.get_score = AsyncMock()

        self.user = Mock()
        self.user.id = 1

        self.attempt_id = uuid4()

    async def test_get_score_success(self):
        score = Mock()
        score.score = 8
        self.service.get_score.return_value = score

        response = await get_score(
            self.attempt_id,
            self.user,
            self.service
        )

        self.service.get_score.assert_awaited_once_with(
            self.attempt_id,
            self.user.id
        )

        assert response.success is True
        assert response.message == "Score fetched successfully"
        assert response.data == score

    async def test_get_score_service_exception(self):
        self.service.get_score.side_effect = Exception("Attempt not found")

        with pytest.raises(Exception, match="Attempt not found"):
            await get_score(
                self.attempt_id,
                self.user,
                self.service
            )


class TestGetReview:

    def setup_method(self):
        self.service = Mock()
        self.service.get_review = AsyncMock()

        self.user = Mock()
        self.user.id = 1

        self.attempt_id = uuid4()

    async def test_get_review_success(self):
        review = Mock()
        self.service.get_review.return_value = review

        response = await get_review(
            self.attempt_id,
            self.user,
            self.service
        )

        self.service.get_review.assert_awaited_once_with(
            self.attempt_id,
            self.user.id
        )

        assert response.success is True
        assert response.message == "Attempt review fetched successfully"
        assert response.data == review

    async def test_get_review_service_exception(self):
        self.service.get_review.side_effect = Exception("Review not found")

        with pytest.raises(Exception, match="Review not found"):
            await get_review(
                self.attempt_id,
                self.user,
                self.service
            )