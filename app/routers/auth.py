from fastapi import APIRouter, Depends
from typing import Annotated
from app.dependencies import get_auth_service
from app.models.dto.auth import RegisterRequest
from app.models.dto.common import APIResponse
from app.models.dto.users import UserResponse
from app.services.auth_service import AuthService
from fastapi.security import OAuth2PasswordRequestForm

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
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthService = Depends(get_auth_service)
):
    token = await service.login(
        form_data.username,
        form_data.password
    )
    return token
