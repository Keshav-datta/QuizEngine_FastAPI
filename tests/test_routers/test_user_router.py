from unittest.mock import Mock
from uuid import uuid4

from app.models.dto.users import UserResponse
from app.routers.user import get_me


class TestGetMe:

    def setup_method(self):
        self.user = Mock()
        self.user.public_id = uuid4()
        self.user.name = "Keshav"
        self.user.email = "keshav@example.com"
        self.user.role = Mock()
        self.user.role.value = "USER"

    async def test_get_me_success(self):
        response = await get_me(self.user)

        assert response.success is True
        assert response.message == "Current user fetched successfully"

        assert isinstance(response.data, UserResponse)
        assert response.data.public_id == self.user.public_id
        assert response.data.name == self.user.name
        assert response.data.email == self.user.email
        assert response.data.role.value == "USER"