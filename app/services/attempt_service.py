from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.exceptions import AttemptAlreadyActive, AttemptExpired, AttemptNotActive
from app.exceptions import AttemptNotFound, AttemptNotOwned, InvalidAnswer
from app.exceptions import QuizEmpty, QuizNotFound, QuizNotPublished
from app.models.db.attempt import Answer, QuizAttempt
from app.models.dto.attempts import AttemptResponse, AttemptResult, ReviewItem, ReviewResponse, ScoreResponse, SubmitAnswerRequest
from app.models.enums_models import AttemptStatus, QuestionType, QuizStatus
from app.repositories.attempt_repository import AttemptRepo
from app.repositories.question_repository import QuestionRepo
from app.repositories.quiz_repository import QuizRepo


class AttemptService:
    def __init__(self, attempt_repo: AttemptRepo, quiz_repo: QuizRepo, question_repo: QuestionRepo):
        self.attempt_repo = attempt_repo
        self.quiz_repo = quiz_repo
        self.question_repo = question_repo

    @staticmethod
    def normalize_answer(answer: str) -> str:
        return " ".join(answer.lower().strip().split())

    @staticmethod
    def now():
        return datetime.now(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def calculate_expiry(started_at: datetime, minutes: int):
        return started_at + timedelta(minutes=minutes)

    @staticmethod
    def is_expired(expires_at: datetime) -> bool:
        return AttemptService.now() >= expires_at

    async def start_quiz(self, quiz_public_id: UUID, user_id: int):
        quiz = await self.quiz_repo.get_by_public_id(quiz_public_id)

        if quiz is None:
            raise QuizNotFound("Quiz not found", "QUIZ_NOT_FOUND")

        if quiz.status != QuizStatus.PUBLISHED:
            raise QuizNotPublished("Quiz is not published", "QUIZ_NOT_PUBLISHED")

        questions = await self.question_repo.get_by_quiz(quiz.id)

        if not questions:
            raise QuizEmpty("Quiz does not have any questions", "QUIZ_EMPTY")

        active = await self.attempt_repo.get_active(quiz.id, user_id)

        if active:
            if self.is_expired(active.expires_at):
                active.status = AttemptStatus.EXPIRED
                active.submitted_at = self.now()
                await self.attempt_repo.db.commit()
            else:
                raise AttemptAlreadyActive("An active attempt already exists", "ATTEMPT_ALREADY_ACTIVE")

        started_at = self.now()
        attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_id=user_id,
            started_at=started_at,
            expires_at=self.calculate_expiry(started_at, quiz.duration_minutes),
        )

        await self.attempt_repo.add(attempt)
        await self.attempt_repo.db.commit()
        await self.attempt_repo.db.refresh(attempt)

        return AttemptResponse(
            public_id=attempt.public_id,
            quiz_id=quiz.public_id,
            started_at=attempt.started_at,
            expires_at=attempt.expires_at,
            score=attempt.score,
            status=attempt.status,
        )

    async def submit_answer(self, attempt_public_id: UUID, data: SubmitAnswerRequest, user_id: int):
        attempt = await self.get_owned_attempt(attempt_public_id, user_id)
        await self.ensure_active(attempt)

        question = await self.question_repo.get_by_public_id(data.question_id)

        if question is None or question.quiz_id != attempt.quiz_id:
            raise InvalidAnswer("Question not found in this quiz", "INVALID_QUESTION")

        is_correct = False
        selected_option_id = None

        if question.type == QuestionType.MCQ:
            try:
                option_public_id = UUID(data.answer)
            except ValueError as exc:
                raise InvalidAnswer("MCQ answer must be an option id", "INVALID_OPTION") from exc

            option = await self.question_repo.get_option_by_public_id(option_public_id)

            if option is None or option.question_id != question.id:
                raise InvalidAnswer("Invalid option", "INVALID_OPTION")

            selected_option_id = option.id
            is_correct = option.is_correct
        else:
            submitted = self.normalize_answer(data.answer)
            expected = self.normalize_answer(question.correct_answer or "")
            is_correct = submitted == expected

        marks = question.marks if is_correct else -question.negative_marks
        answer = await self.attempt_repo.get_answer(attempt.id, question.id)

        if answer:
            attempt.score -= answer.marks_awarded
            answer.selected_option_id = selected_option_id
            answer.answer_text = None if question.type == QuestionType.MCQ else data.answer.strip()
            answer.is_correct = is_correct
            answer.marks_awarded = marks
            answer.is_skipped = False
        else:
            answer = Answer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option_id=selected_option_id,
                answer_text=None if question.type == QuestionType.MCQ else data.answer.strip(),
                is_correct=is_correct,
                marks_awarded=marks,
            )
            await self.attempt_repo.add_answer(answer)

        attempt.score += marks
        await self.attempt_repo.db.commit()
        await self.attempt_repo.db.refresh(attempt)

        return await self.build_attempt_response(attempt)

    async def skip_question(self, attempt_public_id: UUID, question_public_id: UUID, user_id: int):
        attempt = await self.get_owned_attempt(attempt_public_id, user_id)
        await self.ensure_active(attempt)

        question = await self.question_repo.get_by_public_id(question_public_id)

        if question is None or question.quiz_id != attempt.quiz_id:
            raise InvalidAnswer("Question not found in this quiz", "INVALID_QUESTION")

        answer = await self.attempt_repo.get_answer(attempt.id, question.id)

        if answer:
            raise InvalidAnswer("Question already has an answer", "ANSWER_ALREADY_EXISTS")

        answer = Answer(attempt_id=attempt.id, question_id=question.id, is_skipped=True)
        await self.attempt_repo.add_answer(answer)
        await self.attempt_repo.db.commit()
        await self.attempt_repo.db.refresh(attempt)

        return await self.build_attempt_response(attempt)

    async def finalize_attempt(self, attempt_public_id: UUID, user_id: int):
        attempt = await self.get_owned_attempt(attempt_public_id, user_id)

        if attempt.status in (AttemptStatus.COMPLETED, AttemptStatus.EXPIRED):
            return await self.build_attempt_result(attempt)

        now = self.now()
        attempt.status = AttemptStatus.EXPIRED if now >= attempt.expires_at else AttemptStatus.COMPLETED
        attempt.submitted_at = now

        await self.attempt_repo.db.commit()
        await self.attempt_repo.db.refresh(attempt)
        return await self.build_attempt_result(attempt)

    async def get_score(self, attempt_public_id: UUID, user_id: int):
        attempt = await self.get_owned_attempt(attempt_public_id, user_id)

        return ScoreResponse(
            attempt_id=attempt.public_id,
            score=attempt.score,
            status=attempt.status,
        )

    async def get_review(self, attempt_public_id: UUID, user_id: int):
        attempt = await self.get_owned_attempt(attempt_public_id, user_id)
        questions = await self.question_repo.get_by_quiz(attempt.quiz_id)
        answers = await self.attempt_repo.get_answers(attempt.id)
        answer_map = {answer.question_id: answer for answer in answers}
        items = []
        correct_count = 0
        wrong_count = 0

        for question in questions:
            answer = answer_map.get(question.id)
            submitted_answer = None
            correct_answer = question.correct_answer
            is_correct = False
            marks_awarded = 0
            is_skipped = False
            answer_status = "UNANSWERED"

            if answer:
                submitted_answer = answer.answer_text

                if answer.selected_option is not None:
                    submitted_answer = answer.selected_option.option_text

                if question.type == QuestionType.MCQ:
                    correct_option = next((option for option in question.options if option.is_correct), None)
                    correct_answer = correct_option.option_text if correct_option else None

                is_correct = answer.is_correct
                marks_awarded = answer.marks_awarded
                is_skipped = answer.is_skipped
                answer_status = "SKIPPED" if answer.is_skipped else "ANSWERED"

                if answer.is_correct:
                    correct_count += 1
                elif not answer.is_skipped:
                    wrong_count += 1

            items.append(
                ReviewItem(
                    question_id=question.public_id,
                    question_text=question.question_text,
                    submitted_answer=submitted_answer,
                    correct_answer=correct_answer,
                    is_correct=is_correct,
                    marks_awarded=marks_awarded,
                    is_skipped=is_skipped,
                    status=answer_status,
                )
            )

        quiz = await self.quiz_repo.get_by_id(attempt.quiz_id)

        return ReviewResponse(
            attempt_id=attempt.public_id,
            quiz_id=quiz.public_id,
            score=attempt.score,
            status=attempt.status,
            total_questions=len(questions),
            correct_answers=correct_count,
            wrong_answers=wrong_count,
            items=items,
        )

    async def get_owned_attempt(self, attempt_public_id: UUID, user_id: int):
        attempt = await self.attempt_repo.get_by_public_id(attempt_public_id)

        if attempt is None:
            raise AttemptNotFound("Attempt not found", "ATTEMPT_NOT_FOUND")

        if attempt.user_id != user_id:
            raise AttemptNotOwned("This attempt does not belong to you", "ATTEMPT_NOT_OWNED")

        return attempt

    async def build_attempt_response(self, attempt: QuizAttempt):
        quiz = await self.quiz_repo.get_by_id(attempt.quiz_id)

        return AttemptResponse(
            public_id=attempt.public_id,
            quiz_id=quiz.public_id,
            started_at=attempt.started_at,
            expires_at=attempt.expires_at,
            score=attempt.score,
            status=attempt.status,
        )

    async def build_attempt_result(self, attempt: QuizAttempt):
        quiz = await self.quiz_repo.get_by_id(attempt.quiz_id)

        return AttemptResult(
            public_id=attempt.public_id,
            quiz_id=quiz.public_id,
            started_at=attempt.started_at,
            expires_at=attempt.expires_at,
            submitted_at=attempt.submitted_at,
            score=attempt.score,
            status=attempt.status,
        )

    async def ensure_active(self, attempt: QuizAttempt):
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise AttemptNotActive("Attempt is no longer active", "ATTEMPT_NOT_ACTIVE")

        if self.is_expired(attempt.expires_at):
            attempt.status = AttemptStatus.EXPIRED
            attempt.submitted_at = self.now()
            await self.attempt_repo.db.commit()
            raise AttemptExpired("The quiz attempt has expired", "ATTEMPT_EXPIRED")
