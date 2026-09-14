from passlib.context import CryptContext

from app.exceptions import InvalidCredentials, UserAlreadyExists
from app.helpers.security import create_access_token
from app.models.db.user import User
from app.models.dto.auth import RegisterRequest, TokenResponse
from app.models.enums_models import UserRole
from app.repositories.user_repository import UserRepo

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, user_repo: UserRepo):
        self.user_repo = user_repo

    @staticmethod
    def hash_password(password: str) -> str:
        return password_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return password_context.verify(password, hashed_password)

    async def register(self, data: RegisterRequest):
        email = data.email.lower().strip()
        existing = await self.user_repo.get_by_email(email)

        if existing:
            raise UserAlreadyExists("Email already registered", "USER_ALREADY_EXISTS")

        user = User(
            name=data.name,
            email=email,
            password_hash=self.hash_password(data.password),
            role=UserRole.USER,
        )

        await self.user_repo.add(user)
        await self.user_repo.db.commit()
        await self.user_repo.db.refresh(user)

        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_by_email(email.lower().strip())

        if user is None or not self.verify_password(password, user.password_hash):
            raise InvalidCredentials("Invalid email or password", "INVALID_CREDENTIALS")

        return TokenResponse(
            access_token=create_access_token(user.public_id)
        )
