from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.exceptions import InvalidCredentials, UserAlreadyExists
from app.models.dto.auth import RegisterRequest
from app.models.enums_models import UserRole
from app.services.auth_service import AuthService


class TestAuthService:
    def setup_method(self):
        self.repo = Mock()
        self.repo.get_by_email = AsyncMock()
        self.repo.add = AsyncMock()
        self.repo.db = Mock()
        self.repo.db.commit = AsyncMock()
        self.repo.db.refresh = AsyncMock()
        self.service = AuthService(self.repo)

    async def test_register_success(self, monkeypatch):
        self.repo.get_by_email.return_value = None
        monkeypatch.setattr(AuthService, "hash_password", staticmethod(lambda password: f"hash-{password}"))
        data = RegisterRequest(name="Keshav", email=" KESHAV@GMAIL.COM ", password="keshav123")

        user = await self.service.register(data)

        assert user.email == "keshav@gmail.com"
        assert user.password_hash == "hash-keshav123"
        assert user.role == UserRole.USER
        self.repo.add.assert_awaited_once()
        self.repo.db.commit.assert_awaited_once()
        self.repo.db.refresh.assert_awaited_once_with(user)

    async def test_register_existing_email(self):
        self.repo.get_by_email.return_value = SimpleNamespace(email="keshav@gmail.com")
        data = RegisterRequest(name="Keshav", email="keshav@gmail.com", password="keshav123")

        with pytest.raises(UserAlreadyExists):
            await self.service.register(data)

        self.repo.add.assert_not_awaited()
        self.repo.db.commit.assert_not_awaited()

    async def test_login_success(self, monkeypatch):
        user = SimpleNamespace(public_id="public-id", password_hash="hashed")
        self.repo.get_by_email.return_value = user
        monkeypatch.setattr(AuthService, "verify_password", staticmethod(lambda password, hashed: True))
        monkeypatch.setattr("app.services.auth_service.create_access_token", lambda public_id: "jwt-token")

        result = await self.service.login(" KESHAV@GMAIL.COM ", "keshav123")

        assert result.access_token == "jwt-token"
        assert result.token_type == "bearer"
        self.repo.get_by_email.assert_awaited_once_with("keshav@gmail.com")

    async def test_login_invalid_user(self):
        self.repo.get_by_email.return_value = None
        with pytest.raises(InvalidCredentials):
            await self.service.login("keshav@gmail.com", "wrong")

    async def test_login_invalid_password(self, monkeypatch):
        self.repo.get_by_email.return_value = SimpleNamespace(password_hash="hashed")
        monkeypatch.setattr(AuthService, "verify_password", staticmethod(lambda password, hashed: False))

        with pytest.raises(InvalidCredentials):
            await self.service.login("keshav@gmail.com", "wrong")
