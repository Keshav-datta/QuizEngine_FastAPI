from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.models.db.user import User
from app.repositories.user_repository import UserRepo


class TestUserRepo:

    def setup_method(self):
        self.db = Mock()
        self.db.get = AsyncMock()
        self.db.execute = AsyncMock()
        self.db.add = Mock()
        self.db.flush = AsyncMock()

        self.repo = UserRepo(self.db)

    async def test_get_by_id_success(self):
        user = Mock(spec=User)
        user.id = 1

        self.db.get.return_value = user

        result = await self.repo.get_by_id(1)

        self.db.get.assert_awaited_once_with(User, 1)
        assert result == user

    async def test_get_by_id_not_found(self):
        self.db.get.return_value = None

        result = await self.repo.get_by_id(999)

        self.db.get.assert_awaited_once_with(User, 999)
        assert result is None

    async def test_get_by_public_id_success(self):
        public_id = uuid4()
        user = Mock(spec=User)

        result_mock = Mock()
        result_mock.scalar_one_or_none.return_value = user

        self.db.execute.return_value = result_mock

        result = await self.repo.get_by_public_id(public_id)

        self.db.execute.assert_awaited_once()
        result_mock.scalar_one_or_none.assert_called_once_with()

        assert result == user

    async def test_get_by_public_id_not_found(self):
        public_id = uuid4()

        result_mock = Mock()
        result_mock.scalar_one_or_none.return_value = None

        self.db.execute.return_value = result_mock

        result = await self.repo.get_by_public_id(public_id)

        self.db.execute.assert_awaited_once()
        assert result is None

    async def test_get_by_email_success(self):
        email = "keshav@example.com"
        user = Mock(spec=User)

        result_mock = Mock()
        result_mock.scalar_one_or_none.return_value = user

        self.db.execute.return_value = result_mock

        result = await self.repo.get_by_email(email)

        self.db.execute.assert_awaited_once()
        result_mock.scalar_one_or_none.assert_called_once_with()

        assert result == user

    async def test_get_by_email_not_found(self):
        email = "unknown@example.com"

        result_mock = Mock()
        result_mock.scalar_one_or_none.return_value = None

        self.db.execute.return_value = result_mock

        result = await self.repo.get_by_email(email)

        self.db.execute.assert_awaited_once()
        assert result is None

    async def test_add_user(self):
        user = Mock(spec=User)

        result = await self.repo.add(user)

        self.db.add.assert_called_once_with(user)
        self.db.flush.assert_awaited_once()

        assert result == user