from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.user import User


class UserRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int):
        return await self.db.get(User, user_id)

    async def get_by_public_id(self, public_id: UUID):
        result = await self.db.execute(
            select(User).where(User.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str):
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def add(self, user: User):
        self.db.add(user)
        await self.db.flush()
        return user
