from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums_models import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    email: EmailStr
    role: UserRole
