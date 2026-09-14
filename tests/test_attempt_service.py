from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.exceptions import AttemptAlreadyActive, AttemptExpired, AttemptNotActive, AttemptNotFound, AttemptNotOwned, InvalidAnswer, QuizEmpty, QuizNotFound, QuizNotPublished
from app.models.dto.attempts import SubmitAnswerRequest
from app.models.enums_models import AttemptStatus, QuestionType, QuizStatus
from app.services.attempt_service import AttemptService


class TestAttemptService:
    def setup_method(self):
        self.attempt_repo = Mock(); self.quiz_repo = Mock(); self.question_repo = Mock()
        self.attempt_repo.get_by_public_id = AsyncMock(); self.attempt_repo.get_active = AsyncMock(); self.attempt_repo.get_answer = AsyncMock(); self.attempt_repo.add = AsyncMock(); self.attempt_repo.add_answer = AsyncMock(); self.attempt_repo.get_answers = AsyncMock()
        self.attempt_repo.db = Mock(); self.attempt_repo.db.commit = AsyncMock(); self.attempt_repo.db.refresh = AsyncMock()
        self.quiz_repo.get_by_public_id = AsyncMock(); self.quiz_repo.get_by_id = AsyncMock()
        self.question_repo.get_by_quiz = AsyncMock(); self.question_repo.get_by_public_id = AsyncMock(); self.question_repo.get_option_by_public_id = AsyncMock()
        self.service = AttemptService(self.attempt_repo, self.quiz_repo, self.question_repo)
        self.quiz_id = uuid4(); self.attempt_id = uuid4(); self.question_id = uuid4()

    def quiz(self, status=QuizStatus.PUBLISHED, duration=30):
        return SimpleNamespace(id=10, public_id=self.quiz_id, status=status, duration_minutes=duration)

    def attempt(self, status=AttemptStatus.IN_PROGRESS, expires_at=None, user_id=2):
        return SimpleNamespace(id=20, public_id=self.attempt_id, quiz_id=10, user_id=user_id, started_at=datetime(2026, 1, 1, 10), expires_at=expires_at or datetime.now() + timedelta(minutes=20), submitted_at=None, score=0, status=status)

    async def test_start_success(self):
        self.quiz_repo.get_by_public_id.return_value = self.quiz(); self.question_repo.get_by_quiz.return_value = [SimpleNamespace(id=1)]; self.attempt_repo.get_active.return_value = None
        result = await self.service.start_quiz(self.quiz_id, 2)
        assert result.status == AttemptStatus.IN_PROGRESS; assert result.quiz_id == self.quiz_id; assert result.expires_at > result.started_at
        self.attempt_repo.add.assert_awaited_once(); self.attempt_repo.db.commit.assert_awaited_once()

    async def test_start_quiz_not_found(self):
        self.quiz_repo.get_by_public_id.return_value = None
        with pytest.raises(QuizNotFound): await self.service.start_quiz(self.quiz_id, 2)

    async def test_start_quiz_not_published(self):
        self.quiz_repo.get_by_public_id.return_value = self.quiz(QuizStatus.DRAFT)
        with pytest.raises(QuizNotPublished): await self.service.start_quiz(self.quiz_id, 2)
        self.question_repo.get_by_quiz.assert_not_awaited()

    async def test_start_quiz_empty(self):
        self.quiz_repo.get_by_public_id.return_value = self.quiz(); self.question_repo.get_by_quiz.return_value = []
        with pytest.raises(QuizEmpty): await self.service.start_quiz(self.quiz_id, 2)

    async def test_start_rejects_active_attempt(self):
        self.quiz_repo.get_by_public_id.return_value = self.quiz(); self.question_repo.get_by_quiz.return_value = [SimpleNamespace(id=1)]; self.attempt_repo.get_active.return_value = self.attempt()
        with pytest.raises(AttemptAlreadyActive): await self.service.start_quiz(self.quiz_id, 2)
        self.attempt_repo.add.assert_not_awaited()

    async def test_start_expires_old_attempt_and_creates_new_one(self):
        old = self.attempt(expires_at=datetime.now() - timedelta(minutes=1))
        self.quiz_repo.get_by_public_id.return_value = self.quiz(); self.question_repo.get_by_quiz.return_value = [SimpleNamespace(id=1)]; self.attempt_repo.get_active.return_value = old
        result = await self.service.start_quiz(self.quiz_id, 2)
        assert old.status == AttemptStatus.EXPIRED; assert old.submitted_at is not None; assert result.status == AttemptStatus.IN_PROGRESS

    async def test_submit_rejects_missing_attempt(self):
        self.attempt_repo.get_by_public_id.return_value = None
        with pytest.raises(AttemptNotFound): await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer="x"), 2)

    async def test_submit_rejects_other_owner(self):
        self.attempt_repo.get_by_public_id.return_value = self.attempt(user_id=3)
        with pytest.raises(AttemptNotOwned): await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer="x"), 2)

    async def test_submit_rejects_inactive(self):
        self.attempt_repo.get_by_public_id.return_value = self.attempt(AttemptStatus.COMPLETED)
        with pytest.raises(AttemptNotActive): await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer="x"), 2)

    async def test_submit_rejects_expired(self):
        attempt = self.attempt(expires_at=datetime.now() - timedelta(minutes=1)); self.attempt_repo.get_by_public_id.return_value = attempt
        with pytest.raises(AttemptExpired): await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer="x"), 2)
        assert attempt.status == AttemptStatus.EXPIRED

    async def test_submit_rejects_question_not_in_quiz(self):
        self.attempt_repo.get_by_public_id.return_value = self.attempt(); self.question_repo.get_by_public_id.return_value = None
        with pytest.raises(InvalidAnswer): await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer="x"), 2)

    async def test_submit_rejects_question_from_another_quiz(self):
        self.attempt_repo.get_by_public_id.return_value = self.attempt(); self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=30, quiz_id=99, type=QuestionType.SUBJECTIVE)
        with pytest.raises(InvalidAnswer): await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer="x"), 2)

    async def test_mcq_invalid_option_uuid(self):
        self.attempt_repo.get_by_public_id.return_value = self.attempt(); self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=30, quiz_id=10, type=QuestionType.MCQ, marks=2, negative_marks=.5)
        with pytest.raises(InvalidAnswer): await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer="bad"), 2)

    async def test_mcq_missing_option(self):
        self.attempt_repo.get_by_public_id.return_value = self.attempt(); self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=30, quiz_id=10, type=QuestionType.MCQ, marks=2, negative_marks=.5); self.question_repo.get_option_by_public_id.return_value = None
        with pytest.raises(InvalidAnswer): await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer=str(uuid4())), 2)

    async def test_mcq_option_from_another_question(self):
        oid = uuid4(); self.attempt_repo.get_by_public_id.return_value = self.attempt(); self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=30, quiz_id=10, type=QuestionType.MCQ, marks=2, negative_marks=.5); self.question_repo.get_option_by_public_id.return_value = SimpleNamespace(id=40, question_id=99, is_correct=True)
        with pytest.raises(InvalidAnswer): await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer=str(oid)), 2)

    async def test_mcq_correct_adds_marks(self):
        oid = uuid4(); attempt = self.attempt(); self.attempt_repo.get_by_public_id.return_value = attempt; self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=30, quiz_id=10, type=QuestionType.MCQ, marks=2, negative_marks=.5); self.question_repo.get_option_by_public_id.return_value = SimpleNamespace(id=40, question_id=30, is_correct=True); self.attempt_repo.get_answer.return_value = None; self.quiz_repo.get_by_id.return_value = SimpleNamespace(public_id=self.quiz_id)
        await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer=str(oid)), 2)
        assert attempt.score == 2; self.attempt_repo.add_answer.assert_awaited_once()

    async def test_mcq_wrong_applies_negative_marks(self):
        oid = uuid4(); attempt = self.attempt(); self.attempt_repo.get_by_public_id.return_value = attempt; self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=30, quiz_id=10, type=QuestionType.MCQ, marks=2, negative_marks=.5); self.question_repo.get_option_by_public_id.return_value = SimpleNamespace(id=40, question_id=30, is_correct=False); self.attempt_repo.get_answer.return_value = None; self.quiz_repo.get_by_id.return_value = SimpleNamespace(public_id=self.quiz_id)
        await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer=str(oid)), 2)
        assert attempt.score == -.5

    async def test_subjective_normalizes_answer(self):
        attempt = self.attempt(); self.attempt_repo.get_by_public_id.return_value = attempt; self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=30, quiz_id=10, type=QuestionType.SUBJECTIVE, marks=2, negative_marks=0, correct_answer="hello world"); self.attempt_repo.get_answer.return_value = None; self.quiz_repo.get_by_id.return_value = SimpleNamespace(public_id=self.quiz_id)
        await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer=" HELLO   WORLD "), 2)
        assert attempt.score == 2

    async def test_subjective_wrong(self):
        attempt = self.attempt(); self.attempt_repo.get_by_public_id.return_value = attempt; self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=30, quiz_id=10, type=QuestionType.SUBJECTIVE, marks=2, negative_marks=.5, correct_answer="hello"); self.attempt_repo.get_answer.return_value = None; self.quiz_repo.get_by_id.return_value = SimpleNamespace(public_id=self.quiz_id)
        await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer="world"), 2)
        assert attempt.score == -.5

    async def test_submit_updates_existing_answer_and_score(self):
        oid = uuid4(); attempt = self.attempt(); attempt.score = 2; existing = SimpleNamespace(marks_awarded=2, selected_option_id=10, answer_text=None, is_correct=True, is_skipped=False)
        self.attempt_repo.get_by_public_id.return_value = attempt; self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=30, quiz_id=10, type=QuestionType.MCQ, marks=2, negative_marks=.5); self.question_repo.get_option_by_public_id.return_value = SimpleNamespace(id=40, question_id=30, is_correct=False); self.attempt_repo.get_answer.return_value = existing; self.quiz_repo.get_by_id.return_value = SimpleNamespace(public_id=self.quiz_id)
        await self.service.submit_answer(self.attempt_id, SubmitAnswerRequest(question_id=self.question_id, answer=str(oid)), 2)
        assert attempt.score == -.5; assert existing.marks_awarded == -.5; assert existing.is_correct is False; self.attempt_repo.add_answer.assert_not_awaited()

    async def test_skip_success(self):
        attempt = self.attempt(); self.attempt_repo.get_by_public_id.return_value = attempt; self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=30, quiz_id=10); self.attempt_repo.get_answer.return_value = None; self.quiz_repo.get_by_id.return_value = SimpleNamespace(public_id=self.quiz_id)
        result = await self.service.skip_question(self.attempt_id, self.question_id, 2)
        assert result.score == 0; self.attempt_repo.add_answer.assert_awaited_once()

    async def test_skip_invalid_question(self):
        self.attempt_repo.get_by_public_id.return_value = self.attempt(); self.question_repo.get_by_public_id.return_value = None
        with pytest.raises(InvalidAnswer): await self.service.skip_question(self.attempt_id, self.question_id, 2)

    async def test_skip_existing_answer(self):
        self.attempt_repo.get_by_public_id.return_value = self.attempt(); self.question_repo.get_by_public_id.return_value = SimpleNamespace(id=30, quiz_id=10); self.attempt_repo.get_answer.return_value = SimpleNamespace(id=1)
        with pytest.raises(InvalidAnswer): await self.service.skip_question(self.attempt_id, self.question_id, 2)
        self.attempt_repo.add_answer.assert_not_awaited()

    async def test_finalize_active_before_expiry(self):
        attempt = self.attempt(); self.attempt_repo.get_by_public_id.return_value = attempt; self.quiz_repo.get_by_id.return_value = SimpleNamespace(public_id=self.quiz_id)
        result = await self.service.finalize_attempt(self.attempt_id, 2)
        assert attempt.status == AttemptStatus.COMPLETED; assert result.status == AttemptStatus.COMPLETED

    async def test_finalize_expired_active(self):
        attempt = self.attempt(expires_at=datetime.now() - timedelta(minutes=1)); self.attempt_repo.get_by_public_id.return_value = attempt; self.quiz_repo.get_by_id.return_value = SimpleNamespace(public_id=self.quiz_id)
        result = await self.service.finalize_attempt(self.attempt_id, 2)
        assert attempt.status == AttemptStatus.EXPIRED; assert result.status == AttemptStatus.EXPIRED

    async def test_finalize_completed_returns_existing(self):
        attempt = self.attempt(AttemptStatus.COMPLETED); self.attempt_repo.get_by_public_id.return_value = attempt; self.quiz_repo.get_by_id.return_value = SimpleNamespace(public_id=self.quiz_id)
        await self.service.finalize_attempt(self.attempt_id, 2)
        self.attempt_repo.db.commit.assert_not_awaited()

    async def test_finalize_expired_returns_existing(self):
        attempt = self.attempt(AttemptStatus.EXPIRED); self.attempt_repo.get_by_public_id.return_value = attempt; self.quiz_repo.get_by_id.return_value = SimpleNamespace(public_id=self.quiz_id)
        await self.service.finalize_attempt(self.attempt_id, 2)
        self.attempt_repo.db.commit.assert_not_awaited()

    async def test_get_score(self):
        attempt = self.attempt(); attempt.score = 7.5; self.attempt_repo.get_by_public_id.return_value = attempt
        result = await self.service.get_score(self.attempt_id, 2)
        assert result.score == 7.5; assert result.attempt_id == self.attempt_id

    async def test_get_score_rejects_other_user(self):
        self.attempt_repo.get_by_public_id.return_value = self.attempt(user_id=3)
        with pytest.raises(AttemptNotOwned): await self.service.get_score(self.attempt_id, 2)

    async def test_get_review_counts_correct_wrong_skipped_unanswered(self):
        attempt = self.attempt(); q1 = SimpleNamespace(id=1, public_id=uuid4(), type=QuestionType.MCQ, question_text="2+2?", correct_answer=None, options=[SimpleNamespace(option_text="4", is_correct=True)]); q2 = SimpleNamespace(id=2, public_id=uuid4(), type=QuestionType.SUBJECTIVE, question_text="Keyword?", correct_answer="await", options=[]); q3 = SimpleNamespace(id=3, public_id=uuid4(), type=QuestionType.TRUE_FALSE, question_text="Async?", correct_answer="true", options=[])
        correct = SimpleNamespace(question_id=1, answer_text=None, selected_option=SimpleNamespace(option_text="4"), is_correct=True, marks_awarded=1, is_skipped=False); skipped = SimpleNamespace(question_id=2, answer_text=None, selected_option=None, is_correct=False, marks_awarded=0, is_skipped=True)
        self.attempt_repo.get_by_public_id.return_value = attempt; self.question_repo.get_by_quiz.return_value = [q1, q2, q3]; self.attempt_repo.get_answers.return_value = [correct, skipped]; self.quiz_repo.get_by_id.return_value = SimpleNamespace(public_id=self.quiz_id)
        result = await self.service.get_review(self.attempt_id, 2)
        assert result.total_questions == 3; assert result.correct_answers == 1; assert result.wrong_answers == 0; assert result.items[0].submitted_answer == "4"; assert result.items[1].status == "SKIPPED"; assert result.items[2].status == "UNANSWERED"

    async def test_get_review_counts_wrong(self):
        attempt = self.attempt(); q = SimpleNamespace(id=1, public_id=uuid4(), type=QuestionType.SUBJECTIVE, question_text="Keyword?", correct_answer="await", options=[]); wrong = SimpleNamespace(question_id=1, answer_text="async", selected_option=None, is_correct=False, marks_awarded=-.5, is_skipped=False)
        self.attempt_repo.get_by_public_id.return_value = attempt; self.question_repo.get_by_quiz.return_value = [q]; self.attempt_repo.get_answers.return_value = [wrong]; self.quiz_repo.get_by_id.return_value = SimpleNamespace(public_id=self.quiz_id)
        result = await self.service.get_review(self.attempt_id, 2)
        assert result.wrong_answers == 1; assert result.items[0].submitted_answer == "async"

    async def test_get_owned_attempt_success(self):
        attempt = self.attempt(); self.attempt_repo.get_by_public_id.return_value = attempt
        assert await self.service.get_owned_attempt(self.attempt_id, 2) is attempt

    async def test_get_owned_attempt_not_found(self):
        self.attempt_repo.get_by_public_id.return_value = None
        with pytest.raises(AttemptNotFound): await self.service.get_owned_attempt(self.attempt_id, 2)

    async def test_get_owned_attempt_not_owned(self):
        self.attempt_repo.get_by_public_id.return_value = self.attempt(user_id=3)
        with pytest.raises(AttemptNotOwned): await self.service.get_owned_attempt(self.attempt_id, 2)

    async def test_ensure_active_success(self):
        await self.service.ensure_active(self.attempt(expires_at=datetime.now() + timedelta(minutes=5)))

    async def test_ensure_active_rejects_non_active(self):
        with pytest.raises(AttemptNotActive): await self.service.ensure_active(self.attempt(AttemptStatus.COMPLETED))

    def test_normalize_answer(self):
        assert self.service.normalize_answer("  HELLO   WORLD ") == "hello world"

    def test_calculate_expiry(self):
        start = datetime(2026, 1, 1, 10); assert self.service.calculate_expiry(start, 30) == datetime(2026, 1, 1, 10, 30)
