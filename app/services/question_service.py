from uuid import UUID

from app.exceptions import InvalidQuestionData, QuestionNotFound, QuestionNotOwned, QuizNotDraft, QuizNotFound
from app.models.db.question import Question, QuestionOption
from app.models.dto.questions import CreateQuestionRequest
from app.models.db.question import  QuestionType
from app.models.db.quiz import QuizStatus
from app.repositories.question_repository import QuestionRepo
from app.repositories.quiz_repository import QuizRepo


class QuestionService:
    def __init__(self, question_repo: QuestionRepo, quiz_repo: QuizRepo):
        self.question_repo = question_repo
        self.quiz_repo = quiz_repo

    async def add_question(self, quiz_public_id: UUID, data: CreateQuestionRequest, user_id: int):
        quiz = await self.quiz_repo.get_by_public_id(quiz_public_id)

        if quiz is None:
            raise QuizNotFound("Quiz not found", "QUIZ_NOT_FOUND")

        if quiz.owner_id != user_id:
            raise QuestionNotOwned("You do not own this quiz", "QUIZ_NOT_OWNED")

        if quiz.status != QuizStatus.DRAFT:
            raise QuizNotDraft("Published quiz cannot be changed", "QUIZ_NOT_DRAFT")

        self.validate_question(data)

        question = Question(
            quiz_id=quiz.id,
            type=data.type,
            question_text=data.question_text,
            marks=data.marks,
            negative_marks=data.negative_marks,
            correct_answer=data.correct_answer.strip() if data.correct_answer else None,
        )

        question.options = [
            QuestionOption(option_text=option.option_text, is_correct=option.is_correct)
            for option in data.options
        ]

        await self.question_repo.add(question)
        await self.question_repo.db.commit()
        return await self.question_repo.get_by_public_id(question.public_id)

    async def get_questions(self, quiz_public_id: UUID):
        quiz = await self.quiz_repo.get_by_public_id(quiz_public_id)

        if quiz is None:
            raise QuizNotFound("Quiz not found", "QUIZ_NOT_FOUND")

        return await self.question_repo.get_by_quiz(quiz.id)

    async def delete_question(self, question_public_id: UUID, user_id: int):
        question = await self.question_repo.get_by_public_id(question_public_id)

        if question is None:
            raise QuestionNotFound("Question not found", "QUESTION_NOT_FOUND")

        quiz = await self.quiz_repo.get_by_id(question.quiz_id)

        if quiz is None:
            raise QuizNotFound("Quiz not found", "QUIZ_NOT_FOUND")

        if quiz.owner_id != user_id:
            raise QuestionNotOwned("You do not own this quiz", "QUIZ_NOT_OWNED")

        if quiz.status != QuizStatus.DRAFT:
            raise QuizNotDraft("Published quiz cannot be changed", "QUIZ_NOT_DRAFT")

        await self.question_repo.delete(question)
        await self.question_repo.db.commit()

    @staticmethod
    def validate_question(data: CreateQuestionRequest):
        if data.type == QuestionType.MCQ:
            if len(data.options) != 4:
                raise InvalidQuestionData("MCQ must have exactly 4 options", "MCQ_OPTIONS_REQUIRED")

            if sum(option.is_correct for option in data.options) != 1:
                raise InvalidQuestionData("MCQ needs exactly one correct option", "MCQ_CORRECT_OPTION_REQUIRED")

            if data.correct_answer is not None:
                raise InvalidQuestionData("MCQ does not use correct_answer", "MCQ_INVALID_ANSWER")

        if data.type in (QuestionType.TRUE_FALSE, QuestionType.SUBJECTIVE):
            if not data.correct_answer or not data.correct_answer.strip():
                raise InvalidQuestionData("Question needs correct_answer", "CORRECT_ANSWER_REQUIRED")

            if data.options:
                raise InvalidQuestionData("Question cannot have options", "OPTIONS_NOT_ALLOWED")

        if data.type == QuestionType.TRUE_FALSE:
            if data.correct_answer.strip().lower() not in ("true", "false"):
                raise InvalidQuestionData("True/False answer must be true or false", "INVALID_TRUE_FALSE_ANSWER")
