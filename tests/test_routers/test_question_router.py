from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.models.dto.questions import (
    CreateQuestionRequest,
    OptionRequest,
    QuestionResponse,
)
from app.models.db.question import QuestionType
from app.routers.question import (
    add_question,
    get_questions,
    delete_question,
)


class TestAddQuestion:

    def setup_method(self):
        self.service = Mock()
        self.service.add_question = AsyncMock()

        self.user = Mock()
        self.user.id = 1

        self.quiz_id = uuid4()

        self.data = CreateQuestionRequest(
            type=QuestionType.MCQ,
            question_text="What is Python?",
            marks=2,
            negative_marks=0.5,
            options=[
                OptionRequest(
                    option_text="Programming Language",
                    is_correct=True
                ),
                OptionRequest(
                    option_text="Database",
                    is_correct=False
                ),
                OptionRequest(
                    option_text="Operating System",
                    is_correct=False
                ),
                OptionRequest(
                    option_text="Browser",
                    is_correct=False
                ),
            ]
        )

    async def test_add_question_success(self):
        question = Mock()
        question.public_id = uuid4()
        question.type = QuestionType.MCQ
        question.question_text = "What is Python?"
        question.marks = 2
        question.negative_marks = 0.5

        option1 = Mock()
        option1.public_id = uuid4()
        option1.option_text = "Programming Language"

        option2 = Mock()
        option2.public_id = uuid4()
        option2.option_text = "Database"

        question.options = [option1, option2]

        self.service.add_question.return_value = question

        response = await add_question(
            self.quiz_id,
            self.data,
            self.user,
            self.service
        )

        self.service.add_question.assert_awaited_once_with(
            self.quiz_id,
            self.data,
            self.user.id
        )

        assert response.success is True
        assert response.message == "Question added successfully"

        assert isinstance(response.data, QuestionResponse)
        assert response.data.public_id == question.public_id
        assert response.data.question_text == question.question_text
        assert response.data.marks == question.marks
        assert response.data.negative_marks == question.negative_marks

        assert len(response.data.options) == 2
        assert response.data.options[0].public_id == option1.public_id
        assert response.data.options[0].option_text == option1.option_text
        assert response.data.options[1].public_id == option2.public_id
        assert response.data.options[1].option_text == option2.option_text

    async def test_add_question_service_exception(self):
        self.service.add_question.side_effect = Exception("Question creation failed")

        with pytest.raises(Exception, match="Question creation failed"):
            await add_question(
                self.quiz_id,
                self.data,
                self.user,
                self.service
            )


class TestGetQuestions:

    def setup_method(self):
        self.service = Mock()
        self.service.get_questions = AsyncMock()

        self.quiz_id = uuid4()

    async def test_get_questions_success(self):
        question1 = Mock()
        question1.public_id = uuid4()
        question1.type = QuestionType.MCQ
        question1.question_text = "Question 1"
        question1.marks = 2
        question1.negative_marks = 0.5

        option1 = Mock()
        option1.public_id = uuid4()
        option1.option_text = "Option A"

        question1.options = [option1]

        question2 = Mock()
        question2.public_id = uuid4()
        question2.type = QuestionType.MCQ
        question2.question_text = "Question 2"
        question2.marks = 1
        question2.negative_marks = 0

        option2 = Mock()
        option2.public_id = uuid4()
        option2.option_text = "Option B"

        question2.options = [option2]

        self.service.get_questions.return_value = [
            question1,
            question2
        ]

        response = await get_questions(
            self.quiz_id,
            self.service
        )

        self.service.get_questions.assert_awaited_once_with(
            self.quiz_id
        )

        assert response.success is True
        assert response.message == "Questions fetched successfully"

        assert len(response.data) == 2

        assert response.data[0].public_id == question1.public_id
        assert response.data[0].question_text == question1.question_text
        assert response.data[0].options[0].option_text == "Option A"

        assert response.data[1].public_id == question2.public_id
        assert response.data[1].question_text == question2.question_text
        assert response.data[1].options[0].option_text == "Option B"


class TestDeleteQuestion:

    def setup_method(self):
        self.service = Mock()
        self.service.delete_question = AsyncMock()

        self.user = Mock()
        self.user.id = 1

        self.question_id = uuid4()

    async def test_delete_question_success(self):
        self.service.delete_question.return_value = None

        response = await delete_question(
            self.question_id,
            self.user,
            self.service
        )

        self.service.delete_question.assert_awaited_once_with(
            self.question_id,
            self.user.id
        )

        assert response.success is True
        assert response.message == "Question deleted successfully"
        assert response.data is None