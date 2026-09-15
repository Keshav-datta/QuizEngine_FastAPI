from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.db.user import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    email: EmailStr
    role: UserRole
