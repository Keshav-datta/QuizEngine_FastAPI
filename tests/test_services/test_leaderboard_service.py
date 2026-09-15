from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.exceptions import (
    InvalidQuestionData,
    QuestionNotFound,
    QuestionNotOwned,
    QuizNotDraft,
    QuizNotFound,
)
from app.models.enums_models import QuestionType, QuizStatus
from app.services.question_service import QuestionService


class TestQuestionService:

    def setup_method(self):
        self.question_repo = Mock()
        self.quiz_repo = Mock()

        self.quiz_repo.get_by_public_id = AsyncMock()
        self.quiz_repo.get_by_id = AsyncMock()

        self.question_repo.add = AsyncMock()
        self.question_repo.get_by_public_id = AsyncMock()
        self.question_repo.delete = AsyncMock()

        self.question_repo.db = Mock()
        self.question_repo.db.commit = AsyncMock()

        self.service = QuestionService(
            self.question_repo,
            self.quiz_repo
        )

    async def test_add_question_success(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.id = 10
        quiz.owner_id = 1
        quiz.status = QuizStatus.DRAFT

        self.quiz_repo.get_by_public_id.return_value = quiz

        data = Mock()
        data.type = QuestionType.MCQ
        data.question_text = "What is Python?"
        data.marks = 2
        data.negative_marks = 0.5
        data.correct_answer = None

        option1 = Mock()
        option1.option_text = "Language"
        option1.is_correct = True

        option2 = Mock()
        option2.option_text = "Database"
        option2.is_correct = False

        option3 = Mock()
        option3.option_text = "Browser"
        option3.is_correct = False

        option4 = Mock()
        option4.option_text = "OS"
        option4.is_correct = False

        data.options = [
            option1,
            option2,
            option3,
            option4
        ]

        question = Mock()
        self.question_repo.get_by_public_id.return_value = question

        result = await self.service.add_question(
            quiz_id,
            data,
            1
        )

        self.question_repo.add.assert_awaited_once()
        self.question_repo.db.commit.assert_awaited_once()
        self.question_repo.get_by_public_id.assert_awaited_once()

        assert result == question

    async def test_add_question_quiz_not_found(self):
        quiz_id = uuid4()

        self.quiz_repo.get_by_public_id.return_value = None

        data = Mock()

        with pytest.raises(QuizNotFound):
            await self.service.add_question(
                quiz_id,
                data,
                1
            )

        self.question_repo.add.assert_not_awaited()

    async def test_add_question_not_owner(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.owner_id = 2
        quiz.status = QuizStatus.DRAFT

        self.quiz_repo.get_by_public_id.return_value = quiz

        data = Mock()

        with pytest.raises(QuestionNotOwned):
            await self.service.add_question(
                quiz_id,
                data,
                1
            )

        self.question_repo.add.assert_not_awaited()

    async def test_add_question_published_quiz(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.owner_id = 1
        quiz.status = QuizStatus.PUBLISHED

        self.quiz_repo.get_by_public_id.return_value = quiz

        data = Mock()

        with pytest.raises(QuizNotDraft):
            await self.service.add_question(
                quiz_id,
                data,
                1
            )

    async def test_get_questions_success(self):
        quiz_id = uuid4()

        quiz = Mock()
        quiz.id = 10

        self.quiz_repo.get_by_public_id.return_value = quiz

        questions = [Mock(), Mock()]
        self.question_repo.get_by_quiz.return_value = questions

        result = await self.service.get_questions(quiz_id)

        self.question_repo.get_by_quiz.assert_awaited_once_with(10)

        assert result == questions

    async def test_get_questions_quiz_not_found(self):
        quiz_id = uuid4()

        self.quiz_repo.get_by_public_id.return_value = None

        with pytest.raises(QuizNotFound):
            await self.service.get_questions(quiz_id)

    async def test_delete_question_success(self):
        question_id = uuid4()

        question = Mock()
        question.quiz_id = 10

        quiz = Mock()
        quiz.owner_id = 1
        quiz.status = QuizStatus.DRAFT

        self.question_repo.get_by_public_id.return_value = question
        self.quiz_repo.get_by_id.return_value = quiz

        await self.service.delete_question(
            question_id,
            1
        )

        self.question_repo.delete.assert_awaited_once_with(question)
        self.question_repo.db.commit.assert_awaited_once()

    async def test_delete_question_not_found(self):
        question_id = uuid4()

        self.question_repo.get_by_public_id.return_value = None

        with pytest.raises(QuestionNotFound):
            await self.service.delete_question(
                question_id,
                1
            )

        self.question_repo.delete.assert_not_awaited()

    async def test_delete_question_quiz_not_found(self):
        question_id = uuid4()

        question = Mock()
        question.quiz_id = 10

        self.question_repo.get_by_public_id.return_value = question
        self.quiz_repo.get_by_id.return_value = None

        with pytest.raises(QuizNotFound):
            await self.service.delete_question(
                question_id,
                1
            )

    async def test_delete_question_not_owner(self):
        question_id = uuid4()

        question = Mock()
        question.quiz_id = 10

        quiz = Mock()
        quiz.owner_id = 2
        quiz.status = QuizStatus.DRAFT

        self.question_repo.get_by_public_id.return_value = question
        self.quiz_repo.get_by_id.return_value = quiz

        with pytest.raises(QuestionNotOwned):
            await self.service.delete_question(
                question_id,
                1
            )

        self.question_repo.delete.assert_not_awaited()

    async def test_delete_question_published_quiz(self):
        question_id = uuid4()

        question = Mock()
        question.quiz_id = 10

        quiz = Mock()
        quiz.owner_id = 1
        quiz.status = QuizStatus.PUBLISHED

        self.question_repo.get_by_public_id.return_value = question
        self.quiz_repo.get_by_id.return_value = quiz

        with pytest.raises(QuizNotDraft):
            await self.service.delete_question(
                question_id,
                1
            )

        self.question_repo.delete.assert_not_awaited()

    def test_validate_mcq_requires_four_options(self):
        data = Mock()
        data.type = QuestionType.MCQ
        data.options = [Mock(), Mock()]
        data.correct_answer = None

        with pytest.raises(InvalidQuestionData):
            QuestionService.validate_question(data)

    def test_validate_mcq_requires_one_correct_option(self):
        data = Mock()
        data.type = QuestionType.MCQ
        data.options = [
            Mock(is_correct=False),
            Mock(is_correct=False),
            Mock(is_correct=False),
            Mock(is_correct=False)
        ]
        data.correct_answer = None

        with pytest.raises(InvalidQuestionData):
            QuestionService.validate_question(data)

    def test_validate_mcq_rejects_correct_answer(self):
        data = Mock()
        data.type = QuestionType.MCQ
        data.options = [
            Mock(is_correct=True),
            Mock(is_correct=False),
            Mock(is_correct=False),
            Mock(is_correct=False)
        ]
        data.correct_answer = "Python"

        with pytest.raises(InvalidQuestionData):
            QuestionService.validate_question(data)

    def test_validate_true_false_requires_answer(self):
        data = Mock()
        data.type = QuestionType.TRUE_FALSE
        data.options = []
        data.correct_answer = " "

        with pytest.raises(InvalidQuestionData):
            QuestionService.validate_question(data)

    def test_validate_true_false_rejects_invalid_answer(self):
        data = Mock()
        data.type = QuestionType.TRUE_FALSE
        data.options = []
        data.correct_answer = "maybe"

        with pytest.raises(InvalidQuestionData):
            QuestionService.validate_question(data)

    def test_validate_true_false_rejects_options(self):
        data = Mock()
        data.type = QuestionType.TRUE_FALSE
        data.options = [Mock()]
        data.correct_answer = "true"

        with pytest.raises(InvalidQuestionData):
            QuestionService.validate_question(data)

    def test_validate_subjective_requires_answer(self):
        data = Mock()
        data.type = QuestionType.SUBJECTIVE
        data.options = []
        data.correct_answer = ""

        with pytest.raises(InvalidQuestionData):
            QuestionService.validate_question(data)

    def test_validate_subjective_rejects_options(self):
        data = Mock()
        data.type = QuestionType.SUBJECTIVE
        data.options = [Mock()]
        data.correct_answer = "asyncio"

        with pytest.raises(InvalidQuestionData):
            QuestionService.validate_question(data)

    def test_validate_valid_true_false(self):
        data = Mock()
        data.type = QuestionType.TRUE_FALSE
        data.options = []
        data.correct_answer = " TRUE "

        QuestionService.validate_question(data)

    def test_validate_valid_subjective(self):
        data = Mock()
        data.type = QuestionType.SUBJECTIVE
        data.options = []
        data.correct_answer = " async programming "

        QuestionService.validate_question(data)

    def test_validate_valid_mcq(self):
        data = Mock()
        data.type = QuestionType.MCQ
        data.options = [
            Mock(is_correct=True),
            Mock(is_correct=False),
            Mock(is_correct=False),
            Mock(is_correct=False)
        ]
        data.correct_answer = None

        QuestionService.validate_question(data)