from fastapi import APIRouter, Depends

from app.dependencies import get_auth_service
from app.models.dto.auth import LoginRequest, RegisterRequest, TokenResponse
from app.models.dto.common import APIResponse
from app.models.dto.users import UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register")
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_auth_service)
):
    user = await service.register(data)

    return APIResponse(
        success=True,
        message="User registered successfully",
        data=UserResponse.model_validate(user),
    )


@router.post("/login")
async def login(
    data: LoginRequest,
    service: AuthService = Depends(get_auth_service)
):
    token = await service.login(data.email, data.password)

    return APIResponse(
        success=True,
        message="Login successful",
        data=token,
    )
