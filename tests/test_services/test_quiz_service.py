from unittest.mock import AsyncMock, Mock

import pytest

from app.exceptions import InvalidCredentials, UserAlreadyExists
from app.models.db.user import User
from app.models.enums_models import UserRole
from app.services.auth_service import AuthService


class TestAuthService:

    def setup_method(self):
        self.user_repo = Mock()
        self.user_repo.get_by_email = AsyncMock()
        self.user_repo.add = AsyncMock()

        self.user_repo.db = Mock()
        self.user_repo.db.commit = AsyncMock()
        self.user_repo.db.refresh = AsyncMock()

        self.service = AuthService(self.user_repo)

    async def test_register_success(self):
        self.user_repo.get_by_email.return_value = None

        data = Mock()
        data.name = "Keshav"
        data.email = " KESHAV@EXAMPLE.COM "
        data.password = "password123"

        user = await self.service.register(data)

        self.user_repo.get_by_email.assert_awaited_once_with(
            "keshav@example.com"
        )
        self.user_repo.add.assert_awaited_once()
        self.user_repo.db.commit.assert_awaited_once()
        self.user_repo.db.refresh.assert_awaited_once_with(user)

        assert isinstance(user, User)
        assert user.name == "Keshav"
        assert user.email == "keshav@example.com"
        assert user.role == UserRole.USER
        assert user.password_hash != "password123"

        assert AuthService.verify_password(
            "password123",
            user.password_hash
        )

    async def test_register_existing_email(self):
        self.user_repo.get_by_email.return_value = Mock()

        data = Mock()
        data.name = "Keshav"
        data.email = "keshav@example.com"
        data.password = "password123"

        with pytest.raises(UserAlreadyExists):
            await self.service.register(data)

        self.user_repo.get_by_email.assert_awaited_once_with(
            "keshav@example.com"
        )
        self.user_repo.add.assert_not_awaited()
        self.user_repo.db.commit.assert_not_awaited()

    async def test_login_success(self, monkeypatch):
        user = Mock()
        user.password_hash = AuthService.hash_password("password123")
        user.public_id = "user-public-id"

        self.user_repo.get_by_email.return_value = user

        monkeypatch.setattr(
            "app.services.auth_service.create_access_token",
            lambda public_id: "test-token"
        )

        result = await self.service.login(
            " KESHAV@EXAMPLE.COM ",
            "password123"
        )

        self.user_repo.get_by_email.assert_awaited_once_with(
            "keshav@example.com"
        )

        assert result.access_token == "test-token"
        assert result.token_type == "bearer"

    async def test_login_user_not_found(self):
        self.user_repo.get_by_email.return_value = None

        with pytest.raises(InvalidCredentials):
            await self.service.login(
                "keshav@example.com",
                "password123"
            )

        self.user_repo.get_by_email.assert_awaited_once_with(
            "keshav@example.com"
        )

    async def test_login_wrong_password(self):
        user = Mock()
        user.password_hash = AuthService.hash_password("correct-password")

        self.user_repo.get_by_email.return_value = user

        with pytest.raises(InvalidCredentials):
            await self.service.login(
                "keshav@example.com",
                "wrong-password"
            )

    def test_hash_and_verify_password(self):
        password = "password123"

        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert AuthService.verify_password(password, hashed)
        assert not AuthService.verify_password("wrong-password", hashed)