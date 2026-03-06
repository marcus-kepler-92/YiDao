"""
Unit tests for UserRepository

Tests repository methods with mocked database session.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.user import User
from app.repository.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class TestUserRepositoryAdd:
    """Tests for adding users"""

    @pytest.mark.asyncio
    async def test_add_user_success(self, mock_db_session):
        """Should add user to database"""
        repo = UserRepository(mock_db_session)
        user_data = UserCreate(username="newuser", email="new@example.com", password="password123")

        # Mock the database operations
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_db_session.add = MagicMock()
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        await repo.add(user_data)

        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()
        mock_db_session.refresh.assert_called_once()


class TestUserRepositoryFind:
    """Tests for finding users"""

    @pytest.mark.asyncio
    async def test_find_by_id_success(self, mock_db_session, sample_user):
        """Should find user by ID"""
        repo = UserRepository(mock_db_session)
        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_user)
        mock_db_session.execute.return_value = mock_result

        result = await repo.find_by_id(1)

        assert result == sample_user
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, mock_db_session):
        """Should return None if user not found"""
        repo = UserRepository(mock_db_session)
        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute.return_value = mock_result

        result = await repo.find_by_id(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_email(self, mock_db_session, sample_user):
        """Should find user by email"""
        repo = UserRepository(mock_db_session)
        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_user)
        mock_db_session.execute.return_value = mock_result

        result = await repo.find_by_email("test@example.com")

        assert result == sample_user

    @pytest.mark.asyncio
    async def test_find_by_username(self, mock_db_session, sample_user):
        """Should find user by username"""
        repo = UserRepository(mock_db_session)
        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_user)
        mock_db_session.execute.return_value = mock_result

        result = await repo.find_by_username("testuser")

        assert result == sample_user


class TestUserRepositoryFindPaginated:
    """Tests for paginated queries"""

    @pytest.mark.asyncio
    async def test_find_paginated_default(self, mock_db_session, sample_users):
        """Should return paginated users with default params"""
        repo = UserRepository(mock_db_session)

        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar_one = MagicMock(return_value=len(sample_users))

        # Mock data query
        mock_data_result = MagicMock()
        mock_data_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=sample_users))
        )

        mock_db_session.execute = AsyncMock(side_effect=[mock_count_result, mock_data_result])

        users, total = await repo.find_paginated()

        assert len(users) == len(sample_users)
        assert total == len(sample_users)
        assert mock_db_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_find_paginated_with_filters(self, mock_db_session, sample_users):
        """Should apply filters to paginated query"""

        repo = UserRepository(mock_db_session)
        created_start = datetime(2024, 1, 1, tzinfo=timezone.utc)

        mock_count_result = MagicMock()
        mock_count_result.scalar_one = MagicMock(return_value=len(sample_users))
        mock_data_result = MagicMock()
        mock_data_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=sample_users))
        )
        mock_db_session.execute = AsyncMock(side_effect=[mock_count_result, mock_data_result])

        users, total = await repo.find_paginated(
            current=1,
            page_size=10,
            created_at_start=created_start,
            username="test",
            is_active=True,
            sort_by="created_at",
            sort_order="desc",
        )

        assert len(users) == len(sample_users)
        assert total == len(sample_users)


class TestUserRepositoryUpdate:
    """Tests for updating users"""

    @pytest.mark.asyncio
    async def test_update_by_id_success(self, mock_db_session, sample_user):
        """Should update user successfully"""
        repo = UserRepository(mock_db_session)
        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_user)
        mock_db_session.execute.return_value = mock_result

        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        update_data = UserUpdate(username="updateduser")
        result = await repo.update_by_id(1, update_data)

        assert result == sample_user
        mock_db_session.flush.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_by_id_not_found(self, mock_db_session):
        """Should return None if user not found"""
        repo = UserRepository(mock_db_session)
        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute.return_value = mock_result

        update_data = UserUpdate(username="updateduser")
        result = await repo.update_by_id(999, update_data)

        assert result is None


class TestUserRepositoryDelete:
    """Tests for deleting users"""

    @pytest.mark.asyncio
    async def test_remove_by_id_success(self, mock_db_session):
        """Should soft delete user successfully"""
        repo = UserRepository(mock_db_session)
        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        mock_db_session.flush = AsyncMock()

        result = await repo.remove_by_id(1)

        assert result is True
        mock_db_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_by_id_not_found(self, mock_db_session):
        """Should return False if user not found"""
        repo = UserRepository(mock_db_session)
        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db_session.execute.return_value = mock_result
        mock_db_session.flush = AsyncMock()

        result = await repo.remove_by_id(999)

        assert result is False

    @pytest.mark.asyncio
    async def test_restore_by_id_success(self, mock_db_session, sample_user):
        """Should restore deleted user successfully"""
        repo = UserRepository(mock_db_session)

        # Mock update result
        mock_update_result = MagicMock()
        mock_update_result.rowcount = 1

        # Mock find result
        mock_find_result = MagicMock()
        mock_find_result.scalar_one_or_none = MagicMock(return_value=sample_user)

        mock_db_session.execute = AsyncMock(side_effect=[mock_update_result, mock_find_result])
        mock_db_session.flush = AsyncMock()

        result = await repo.restore_by_id(1)

        assert result == sample_user
        assert mock_db_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_restore_by_id_not_found(self, mock_db_session):
        """Should return None if user not found or not deleted"""
        repo = UserRepository(mock_db_session)
        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db_session.execute.return_value = mock_result
        mock_db_session.flush = AsyncMock()

        result = await repo.restore_by_id(999)

        assert result is None
