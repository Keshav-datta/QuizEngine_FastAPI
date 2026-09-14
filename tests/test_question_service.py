from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.exceptions import InvalidQuestionData, QuestionNotFound, QuestionNotOwned, QuizNotDraft, QuizNotFound
from app.models.dto.questions import CreateQuestionRequest, OptionRequest
from app.models.enums_models import QuestionType, QuizStatus
from app.services.question_service import QuestionService


def mcq_request():
    return CreateQuestionRequest(
        type=QuestionType.MCQ,
        question_text="2 + 2 = ?",
        marks=2,
        negative_marks=0.5,
        options=[OptionRequest(option_text="3"), OptionRequest(option_text="4", is_correct=True), OptionRequest(option_text="5"), OptionRequest(option_text="6")]
    )


class TestQuestionService:
    def setup_method(self):
        self.question_repo = Mock()
        self.quiz_repo = Mock()
        self.question_repo.add = AsyncMock()
        self.question_repo.get_by_public_id = AsyncMock()
        self.question_repo.get_by_quiz = AsyncMock()
        self.question_repo.delete = AsyncMock()
        self.question_repo.db = Mock()
        self.question_repo.db.commit = AsyncMock()
        self.quiz_repo.get_by_public_id = AsyncMock()
        self.quiz_repo.get_by_id = AsyncMock()
        self.service = QuestionService(self.question_repo, self.quiz_repo)
        self.quiz_id = uuid4()
        self.question_id = uuid4()

    async def test_add_question_success(self):
        quiz = SimpleNamespace(id=10, public_id=self.quiz_id, owner_id=2, status=QuizStatus.DRAFT)
        self.quiz_repo.get_by_public_id.return_value = quiz
        self.question_repo.add.side_effect = lambda question: setattr(question, "public_id", self.question_id)
        self.question_repo.get_by_public_id.side_effect = lambda public_id: SimpleNamespace(
            public_id=public_id, quiz_id=10, type=QuestionType.MCQ, question_text="2 + 2 = ?", marks=2, negative_marks=0.5, options=[]
        )

        result = await self.service.add_question(self.quiz_id, mcq_request(), 2)
        assert result.public_id == self.question_id
        assert result.quiz_id == 10
        self.question_repo.add.assert_awaited_once()
        self.question_repo.db.commit.assert_awaited_once()

    async def test_add_question_quiz_not_found(self):
        self.quiz_repo.get_by_public_id.return_value = None
        with pytest.raises(QuizNotFound):
            await self.service.add_question(self.quiz_id, mcq_request(), 2)

    async def test_add_question_not_owned(self):
        self.quiz_repo.get_by_public_id.return_value = SimpleNamespace(id=10, owner_id=3, status=QuizStatus.DRAFT)
        with pytest.raises(QuestionNotOwned):
            await self.service.add_question(self.quiz_id, mcq_request(), 2)

    async def test_add_question_published_quiz(self):
        self.quiz_repo.get_by_public_id.return_value = SimpleNamespace(id=10, owner_id=2, status=QuizStatus.PUBLISHED)
        with pytest.raises(QuizNotDraft):
            await self.service.add_question(self.quiz_id, mcq_request(), 2)

    async def test_get_questions_success(self):
        self.quiz_repo.get_by_public_id.return_value = SimpleNamespace(id=10)
        questions = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        self.question_repo.get_by_quiz.return_value = questions
        assert await self.service.get_questions(self.quiz_id) == questions

    async def test_get_questions_quiz_not_found(self):
        self.quiz_repo.get_by_public_id.return_value = None
        with pytest.raises(QuizNotFound):
            await self.service.get_questions(self.quiz_id)

    async def test_delete_question_success(self):
        question = SimpleNamespace(id=10, quiz_id=20)
        self.question_repo.get_by_public_id.return_value = question
        self.quiz_repo.get_by_id.return_value = SimpleNamespace(owner_id=2, status=QuizStatus.DRAFT)
        await self.service.delete_question(self.question_id, 2)
        self.question_repo.delete.assert_awaited_once_with(question)
        self.question_repo.db.commit.assert_awaited_once()

    async def test_delete_question_not_found(self):
        self.question_repo.get_by_public_id.return_value = None
        with pytest.raises(QuestionNotFound):
            await self.service.delete_question(self.question_id, 2)

    async def test_delete_question_quiz_not_found(self):
        self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=10, quiz_id=20)
        self.quiz_repo.get_by_id.return_value = None
        with pytest.raises(QuizNotFound):
            await self.service.delete_question(self.question_id, 2)

    async def test_delete_question_not_owned(self):
        self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=10, quiz_id=20)
        self.quiz_repo.get_by_id.return_value = SimpleNamespace(owner_id=3, status=QuizStatus.DRAFT)
        with pytest.raises(QuestionNotOwned):
            await self.service.delete_question(self.question_id, 2)

    async def test_delete_question_published_quiz(self):
        self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=10, quiz_id=20)
        self.quiz_repo.get_by_id.return_value = SimpleNamespace(owner_id=2, status=QuizStatus.PUBLISHED)
        with pytest.raises(QuizNotDraft):
            await self.service.delete_question(self.question_id, 2)

    def test_mcq_requires_four_options(self):
        data = mcq_request(); data.options = data.options[:3]
        with pytest.raises(InvalidQuestionData): QuestionService.validate_question(data)

    def test_mcq_requires_one_correct_option(self):
        data = mcq_request(); data.options[1].is_correct = False
        with pytest.raises(InvalidQuestionData): QuestionService.validate_question(data)

    def test_mcq_rejects_multiple_correct_options(self):
        data = mcq_request(); data.options[0].is_correct = True
        with pytest.raises(InvalidQuestionData): QuestionService.validate_question(data)

    def test_mcq_rejects_correct_answer(self):
        data = mcq_request(); data.correct_answer = "4"
        with pytest.raises(InvalidQuestionData): QuestionService.validate_question(data)

    def test_valid_true_false(self):
        QuestionService.validate_question(CreateQuestionRequest(type=QuestionType.TRUE_FALSE, question_text="Python is a language.", marks=1, negative_marks=0, correct_answer="true"))

    def test_true_false_requires_answer(self):
        data = CreateQuestionRequest(type=QuestionType.TRUE_FALSE, question_text="Python?", marks=1, negative_marks=0)
        with pytest.raises(InvalidQuestionData): QuestionService.validate_question(data)

    def test_true_false_rejects_options(self):
        data = CreateQuestionRequest(type=QuestionType.TRUE_FALSE, question_text="Python?", marks=1, negative_marks=0, correct_answer="true", options=[OptionRequest(option_text="true")])
        with pytest.raises(InvalidQuestionData): QuestionService.validate_question(data)

    def test_true_false_rejects_invalid_answer(self):
        data = CreateQuestionRequest(type=QuestionType.TRUE_FALSE, question_text="Python?", marks=1, negative_marks=0, correct_answer="yes")
        with pytest.raises(InvalidQuestionData): QuestionService.validate_question(data)

    def test_valid_subjective(self):
        QuestionService.validate_question(CreateQuestionRequest(type=QuestionType.SUBJECTIVE, question_text="What is Python?", marks=1, negative_marks=0, correct_answer="language"))

    def test_subjective_requires_answer(self):
        data = CreateQuestionRequest(type=QuestionType.SUBJECTIVE, question_text="What is Python?", marks=1, negative_marks=0)
        with pytest.raises(InvalidQuestionData): QuestionService.validate_question(data)

    def test_subjective_rejects_options(self):
        data = CreateQuestionRequest(type=QuestionType.SUBJECTIVE, question_text="What is Python?", marks=1, negative_marks=0, correct_answer="language", options=[OptionRequest(option_text="A")])
        with pytest.raises(InvalidQuestionData): QuestionService.validate_question(data)
