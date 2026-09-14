from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.db.user import User
from app.models.dto.common import APIResponse
from app.models.dto.users import UserResponse

router = APIRouter()


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return APIResponse(
        success=True,
        message="Current user fetched successfully",
        data=UserResponse.model_validate(current_user),
    )
