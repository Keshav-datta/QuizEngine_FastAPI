from uuid import UUID

from app.exceptions import QuizEmpty, QuizNotDraft, QuizNotFound, QuizNotOwned
from app.models.db.quiz import Quiz
from app.models.dto.quizzes import CreateQuizRequest, UpdateQuizRequest
from app.models.db.quiz import QuizStatus
from app.repositories.question_repository import QuestionRepo
from app.repositories.quiz_repository import QuizRepo


class QuizService:
    def __init__(self, quiz_repo: QuizRepo, question_repo: QuestionRepo):
        self.quiz_repo = quiz_repo
        self.question_repo = question_repo

    async def create_quiz(self, data: CreateQuizRequest, user_id: int):
        quiz = Quiz(
            title=data.title,
            description=data.description,
            duration_minutes=data.duration_minutes,
            owner_id=user_id,
        )

        await self.quiz_repo.add(quiz)
        await self.quiz_repo.db.commit()
        await self.quiz_repo.db.refresh(quiz)
        return quiz

    async def get_all_quizzes(self):
        return await self.quiz_repo.get_all()

    async def get_published_quizzes(self):
        return await self.quiz_repo.get_published()

    async def get_quiz(self, quiz_public_id: UUID):
        quiz = await self.quiz_repo.get_by_public_id(quiz_public_id)

        if quiz is None:
            raise QuizNotFound("Quiz not found", "QUIZ_NOT_FOUND")

        return quiz

    async def update_quiz(self, quiz_public_id: UUID, data: UpdateQuizRequest, user_id: int):
        quiz = await self.get_quiz(quiz_public_id)
        self.check_owner(quiz, user_id)

        if quiz.status != QuizStatus.DRAFT:
            raise QuizNotDraft("Only draft quizzes can be changed", "QUIZ_NOT_DRAFT")

        values = data.model_dump(exclude_unset=True)
        publish = values.pop("status", None) == QuizStatus.PUBLISHED

        for field, value in values.items():
            setattr(quiz, field, value)

        if publish:
            questions = await self.question_repo.get_by_quiz(quiz.id)

            if not questions:
                raise QuizEmpty("Quiz does not have any questions", "QUIZ_EMPTY")

            quiz.status = QuizStatus.PUBLISHED

        await self.quiz_repo.db.commit()
        await self.quiz_repo.db.refresh(quiz)
        return quiz

    async def delete_quiz(self, quiz_public_id: UUID, user_id: int):
        quiz = await self.get_quiz(quiz_public_id)
        self.check_owner(quiz, user_id)

        if quiz.status != QuizStatus.DRAFT:
            raise QuizNotDraft("Only draft quizzes can be deleted", "QUIZ_NOT_DRAFT")

        await self.quiz_repo.delete(quiz)
        await self.quiz_repo.db.commit()

    @staticmethod
    def check_owner(quiz: Quiz, user_id: int):
        if quiz.owner_id != user_id:
            raise QuizNotOwned("You do not own this quiz", "QUIZ_NOT_OWNED")
