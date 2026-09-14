from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_leaderboard_service
from app.models.db.user import User
from app.models.dto.common import APIResponse
from app.services.leaderboard_service import LeaderboardService

router = APIRouter()


@router.get("/quizzes/{quiz_id}/leaderboard")
async def get_leaderboard(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service)
):
    entries = await service.get_leaderboard(quiz_id)

    return APIResponse(
        success=True,
        message="Leaderboard fetched successfully",
        data=entries,
    )
