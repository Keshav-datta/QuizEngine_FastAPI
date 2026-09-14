from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_quiz_service,get_admin
from app.models.db.user import User
from app.models.dto.common import APIResponse
from app.models.dto.quizzes import CreateQuizRequest, QuizResponse, UpdateQuizRequest
from app.services.quiz_service import QuizService

router = APIRouter()


@router.post("")
async def create_quiz(
    data: CreateQuizRequest,
    current_user: User = Depends(get_admin),
    service: QuizService = Depends(get_quiz_service)
):
    quiz = await service.create_quiz(data, current_user.id)

    return APIResponse(
        success=True,
        message="Quiz created successfully",
        data=QuizResponse.model_validate(quiz),
    )


@router.get("")
async def get_quizzes(
    service: QuizService = Depends(get_quiz_service),
    current_user: User = Depends(get_current_user),
):
    quizzes = await service.get_quizzes()

    return APIResponse(
        success=True,
        message="Quizzes fetched successfully",
        data=[QuizResponse.model_validate(quiz) for quiz in quizzes],
    )


@router.get("/{quiz_id}")
async def get_quiz(
    quiz_id: UUID,
    service: QuizService = Depends(get_quiz_service),
    current_user: User = Depends(get_current_user),
):
    quiz = await service.get_quiz(quiz_id)

    return APIResponse(
        success=True,
        message="Quiz fetched successfully",
        data=QuizResponse.model_validate(quiz),
    )


@router.patch("/{quiz_id}")
async def update_quiz(
    quiz_id: UUID,
    data: UpdateQuizRequest,
    current_user: User = Depends(get_admin),
    service: QuizService = Depends(get_quiz_service)
):
    quiz = await service.update_quiz(
        quiz_id,
        data,
        current_user.id,
    )

    return APIResponse(
        success=True,
        message="Quiz updated successfully",
        data=QuizResponse.model_validate(quiz),
    )


@router.delete("/{quiz_id}")
async def delete_quiz(
    quiz_id: UUID,
    current_user: User = Depends(get_admin),
    service: QuizService = Depends(get_quiz_service)
):
    await service.delete_quiz(quiz_id, current_user.id)

    return APIResponse(
        success=True,
        message="Quiz deleted successfully",
        data=None,
    )
