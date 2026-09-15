from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.models.dto.auth import LoginRequest, RegisterRequest
from app.models.dto.users import UserResponse
from app.models.dto.auth import TokenResponse
from app.routers.auth import login, register


class TestRegister:

    def setup_method(self):
        self.service = Mock()
        self.service.register = AsyncMock()

        self.data = RegisterRequest(
            name="Keshav",
            email="keshav@example.com",
            password="password123"
        )

    async def test_register_success(self):
        user = Mock()
        user.public_id = uuid4()
        user.name = "Keshav"
        user.email = "keshav@example.com"
        user.role = Mock()
        user.role.value = "USER"

        self.service.register.return_value = user

        response = await register(self.data, self.service)

        self.service.register.assert_awaited_once_with(self.data)

        assert response.success is True
        assert response.message == "User registered successfully"
        assert isinstance(response.data, UserResponse)
        assert response.data.public_id == user.public_id
        assert response.data.name == user.name
        assert response.data.email == user.email
        assert response.data.role.value == "USER"

    async def test_register_service_exception(self):
        self.service.register.side_effect = Exception("Registration failed")

        with pytest.raises(Exception, match="Registration failed"):
            await register(self.data, self.service)

        self.service.register.assert_awaited_once_with(self.data)


class TestLogin:

    def setup_method(self):
        self.service = Mock()
        self.service.login = AsyncMock()

        self.data = LoginRequest(
            email="keshav@example.com",
            password="password123"
        )

    async def test_login_success(self):
        token = TokenResponse(
            access_token="test-token",
            token_type="bearer"
        )

        self.service.login.return_value = token

        response = await login(self.data, self.service)

        self.service.login.assert_awaited_once_with(
            self.data.email,
            self.data.password
        )

        assert response.success is True
        assert response.message == "Login successful"
        assert response.data == token

    async def test_login_service_exception(self):
        self.service.login.side_effect = Exception("Invalid credentials")

        with pytest.raises(Exception, match="Invalid credentials"):
            await login(self.data, self.service)

        self.service.login.assert_awaited_once_with(
            self.data.email,
            self.data.password
        )