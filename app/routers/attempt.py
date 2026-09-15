from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import get_attempt_service, get_current_user
from app.models.db.user import User
from app.models.dto.attempts import AttemptResponse, ReviewResponse, ScoreResponse, SubmitAnswerRequest
from app.models.dto.common import APIResponse
from app.services.attempt_service import AttemptService

router = APIRouter()


@router.post("/quizzes/{quiz_id}/start")
async def start_quiz(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AttemptService = Depends(get_attempt_service)
):
    attempt = await service.start_quiz(quiz_id, current_user.id)

    return APIResponse(
        success=True,
        message="Quiz attempt started successfully",
        data=attempt,
    )


@router.post("/attempts/{attempt_id}/answer")
async def submit_answer(
    attempt_id: UUID,
    data: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    service: AttemptService = Depends(get_attempt_service)
):
    attempt = await service.submit_answer(
        attempt_id,
        data,
        current_user.id,
    )

    return APIResponse(
        success=True,
        message="Answer submitted successfully",
        data=attempt,
    )


@router.post("/attempts/{attempt_id}/skip")
async def skip_question(
    attempt_id: UUID,
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AttemptService = Depends(get_attempt_service)
):
    attempt = await service.skip_question(
        attempt_id,
        question_id,
        current_user.id,
    )

    return APIResponse(
        success=True,
        message="Question skipped successfully",
        data=attempt,
    )

@router.post("/attempts/{attempt_id}/submit")
async def submit_quiz(
    attempt_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AttemptService = Depends(get_attempt_service)
):
    result = await service.finalize_attempt(
        attempt_id,
        current_user.id,
    )

    return APIResponse(
        success=True,
        message="Quiz submitted successfully",
        data=result,
    )


@router.get("/attempts/{attempt_id}/score")
async def get_score(
    attempt_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AttemptService = Depends(get_attempt_service)
):
    score = await service.get_score(attempt_id, current_user.id)

    return APIResponse(
        success=True,
        message="Score fetched successfully",
        data=score,
    )


@router.get("/attempts/{attempt_id}/review")
async def get_review(
    attempt_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AttemptService = Depends(get_attempt_service)
):
    review = await service.get_review(
        attempt_id,
        current_user.id,
    )

    return APIResponse(
        success=True,
        message="Attempt review fetched successfully",
        data=review,
    )
