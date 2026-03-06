"""
Unit tests for UserService
"""

from unittest.mock import MagicMock

import pytest

from app.exceptions import ConflictException, NotFoundException
from app.schemas.user import UserCreate, UserUpdate


class TestUserServiceCreate:
    """Tests for user creation"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_user_repository, sample_user):
        """Should create user successfully"""
        user_data = UserCreate(username="newuser", email="new@example.com", password="password123")

        result = await user_service.create_user(user_data)

        assert result == sample_user
        mock_user_repository.add.assert_called_once_with(user_data)

    @pytest.mark.asyncio
    async def test_create_user_email_exists(self, user_service, mock_user_repository, sample_user):
        """Should raise error if email already exists"""
        mock_user_repository.find_by_email.return_value = sample_user

        user_data = UserCreate(
            username="newuser", email="existing@example.com", password="password123"
        )

        with pytest.raises(ConflictException) as exc_info:
            await user_service.create_user(user_data)

        assert exc_info.value.status_code == 409
        assert "邮箱" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_create_user_username_exists(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should raise error if username already exists"""
        mock_user_repository.find_by_email.return_value = None
        mock_user_repository.find_by_username.return_value = sample_user

        user_data = UserCreate(
            username="existinguser", email="new@example.com", password="password123"
        )

        with pytest.raises(ConflictException) as exc_info:
            await user_service.create_user(user_data)

        assert exc_info.value.status_code == 409
        assert "用户名" in exc_info.value.message


class TestUserServiceGet:
    """Tests for getting users"""

    @pytest.mark.asyncio
    async def test_get_user_success(self, user_service, mock_user_repository, sample_user):
        """Should get user by ID successfully"""
        result = await user_service.get_user(1)

        from app.schemas.user import UserResponse

        expected = UserResponse.model_validate(sample_user)
        assert result == expected
        mock_user_repository.find_by_id.assert_called()

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, user_service, mock_user_repository):
        """Should raise error if user not found"""
        mock_user_repository.find_by_id.return_value = None

        with pytest.raises(NotFoundException) as exc_info:
            await user_service.get_user(999)

        assert exc_info.value.status_code == 404
        assert "用户" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_get_user_list(self, user_service, mock_user_repository, sample_users):
        """Should get paginated user list"""
        users, total = await user_service.get_user_list(current=1, pageSize=10)

        assert len(users) == len(sample_users)
        assert total == len(sample_users)
        # Check that find_paginated was called with default query params
        call_args = mock_user_repository.find_paginated.call_args
        assert call_args.kwargs["current"] == 1
        assert call_args.kwargs["page_size"] == 10

    @pytest.mark.asyncio
    async def test_get_user_list_with_date_filters(
        self, user_service, mock_user_repository, sample_users
    ):
        """Should get user list filtered by created_at range"""
        from datetime import datetime, timezone

        from app.schemas.user import UserListQueryParams

        created_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        created_end = datetime(2024, 12, 31, tzinfo=timezone.utc)
        query_params = UserListQueryParams(
            created_at_start=created_start, created_at_end=created_end
        )

        users, total = await user_service.get_user_list(
            current=1, pageSize=10, query_params=query_params
        )

        assert len(users) == len(sample_users)
        call_args = mock_user_repository.find_paginated.call_args
        assert call_args.kwargs["created_at_start"] == created_start
        assert call_args.kwargs["created_at_end"] == created_end

    @pytest.mark.asyncio
    async def test_get_user_list_with_search(
        self, user_service, mock_user_repository, sample_users
    ):
        """Should get user list filtered by username search"""
        from app.schemas.user import UserListQueryParams

        query_params = UserListQueryParams(username="admin")

        users, total = await user_service.get_user_list(
            current=1, pageSize=10, query_params=query_params
        )

        assert len(users) == len(sample_users)
        call_args = mock_user_repository.find_paginated.call_args
        assert call_args.kwargs["username"] == "admin"

    @pytest.mark.asyncio
    async def test_get_user_list_with_status_filter(
        self, user_service, mock_user_repository, sample_users
    ):
        """Should get user list filtered by is_active status"""
        from app.schemas.user import UserListQueryParams

        query_params = UserListQueryParams(is_active=True)

        users, total = await user_service.get_user_list(
            current=1, pageSize=10, query_params=query_params
        )

        assert len(users) == len(sample_users)
        call_args = mock_user_repository.find_paginated.call_args
        assert call_args.kwargs["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_user_list_with_sorting(
        self, user_service, mock_user_repository, sample_users
    ):
        """Should get user list sorted by created_at descending"""
        from app.schemas.user import UserListQueryParams

        query_params = UserListQueryParams(sort_by="created_at", sort_order="desc")

        users, total = await user_service.get_user_list(
            current=1, pageSize=10, query_params=query_params
        )

        assert len(users) == len(sample_users)
        call_args = mock_user_repository.find_paginated.call_args
        assert call_args.kwargs["sort_by"] == "created_at"
        assert call_args.kwargs["sort_order"] == "desc"

    @pytest.mark.asyncio
    async def test_get_user_list_with_all_filters(
        self, user_service, mock_user_repository, sample_users
    ):
        """Should get user list with all filters combined"""
        from datetime import datetime, timezone

        from app.schemas.user import UserListQueryParams

        query_params = UserListQueryParams(
            created_at_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            created_at_end=datetime(2024, 12, 31, tzinfo=timezone.utc),
            username="test",
            email="example.com",
            is_active=True,
            sort_by="updated_at",
            sort_order="asc",
        )

        users, total = await user_service.get_user_list(
            current=2, pageSize=20, query_params=query_params
        )

        assert len(users) == len(sample_users)
        call_args = mock_user_repository.find_paginated.call_args
        assert call_args.kwargs["current"] == 2
        assert call_args.kwargs["page_size"] == 20
        assert call_args.kwargs["username"] == "test"
        assert call_args.kwargs["email"] == "example.com"
        assert call_args.kwargs["is_active"] is True
        assert call_args.kwargs["sort_by"] == "updated_at"
        assert call_args.kwargs["sort_order"] == "asc"

    @pytest.mark.asyncio
    async def test_get_user_list_with_updated_at_filters(
        self, user_service, mock_user_repository, sample_users
    ):
        """Should get user list filtered by updated_at range"""
        from datetime import datetime, timezone

        from app.schemas.user import UserListQueryParams

        updated_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        updated_end = datetime(2024, 12, 31, tzinfo=timezone.utc)
        query_params = UserListQueryParams(
            updated_at_start=updated_start, updated_at_end=updated_end
        )

        users, total = await user_service.get_user_list(
            current=1, pageSize=10, query_params=query_params
        )

        assert len(users) == len(sample_users)
        call_args = mock_user_repository.find_paginated.call_args
        assert call_args.kwargs["updated_at_start"] == updated_start
        assert call_args.kwargs["updated_at_end"] == updated_end

    @pytest.mark.asyncio
    async def test_get_user_list_with_email_search(
        self, user_service, mock_user_repository, sample_users
    ):
        """Should get user list filtered by email search"""
        from app.schemas.user import UserListQueryParams

        query_params = UserListQueryParams(email="example.com")

        users, total = await user_service.get_user_list(
            current=1, pageSize=10, query_params=query_params
        )

        assert len(users) == len(sample_users)
        call_args = mock_user_repository.find_paginated.call_args
        assert call_args.kwargs["email"] == "example.com"

    @pytest.mark.asyncio
    async def test_get_user_list_with_ascending_sort(
        self, user_service, mock_user_repository, sample_users
    ):
        """Should get user list sorted ascending"""
        from app.schemas.user import UserListQueryParams

        query_params = UserListQueryParams(sort_by="username", sort_order="asc")

        users, total = await user_service.get_user_list(
            current=1, pageSize=10, query_params=query_params
        )

        assert len(users) == len(sample_users)
        call_args = mock_user_repository.find_paginated.call_args
        assert call_args.kwargs["sort_by"] == "username"
        assert call_args.kwargs["sort_order"] == "asc"

    @pytest.mark.asyncio
    async def test_get_user_list_without_query_params(
        self, user_service, mock_user_repository, sample_users
    ):
        """Should get user list with default query params when None provided"""
        users, total = await user_service.get_user_list(current=1, pageSize=10, query_params=None)

        assert len(users) == len(sample_users)
        call_args = mock_user_repository.find_paginated.call_args
        # Should use default values from UserListQueryParams
        assert call_args.kwargs["sort_by"] == "id"
        assert call_args.kwargs["sort_order"] == "desc"


class TestUserServiceUpdate:
    """Tests for updating users"""

    @pytest.mark.asyncio
    async def test_update_user_success(self, user_service, mock_user_repository, sample_user):
        """Should update user successfully"""
        update_data = UserUpdate(username="updateduser")

        result = await user_service.update_user(1, update_data)

        assert result == sample_user
        mock_user_repository.update_by_id.assert_called_once_with(1, update_data)

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_service, mock_user_repository):
        """Should raise error if user not found"""
        mock_user_repository.find_by_id.return_value = None

        update_data = UserUpdate(username="updateduser")

        with pytest.raises(NotFoundException) as exc_info:
            await user_service.update_user(999, update_data)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user_email_conflict(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should raise error if new email already exists"""
        existing_user = MagicMock()
        existing_user.email = "other@example.com"
        mock_user_repository.find_by_email.return_value = existing_user

        update_data = UserUpdate(email="other@example.com")

        with pytest.raises(ConflictException) as exc_info:
            await user_service.update_user(1, update_data)

        assert exc_info.value.status_code == 409
        assert "邮箱" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_update_user_username_conflict(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should raise error if new username already exists"""
        sample_user.username = "olduser"
        existing_user = MagicMock()
        existing_user.username = "newuser"
        mock_user_repository.find_by_username.return_value = existing_user

        update_data = UserUpdate(username="newuser")

        with pytest.raises(ConflictException) as exc_info:
            await user_service.update_user(1, update_data)

        assert exc_info.value.status_code == 409
        assert "用户名" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_update_user_same_email_no_conflict(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should allow updating with same email"""
        sample_user.email = "same@example.com"
        mock_user_repository.find_by_email.return_value = None  # No conflict

        update_data = UserUpdate(email="same@example.com")

        result = await user_service.update_user(1, update_data)
        assert result == sample_user
        # Should not check for email conflict if email unchanged

    @pytest.mark.asyncio
    async def test_update_user_same_username_no_conflict(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should allow updating with same username"""
        sample_user.username = "sameuser"
        mock_user_repository.find_by_username.return_value = None

        update_data = UserUpdate(username="sameuser")

        result = await user_service.update_user(1, update_data)
        assert result == sample_user


class TestUserServiceDelete:
    """Tests for deleting users"""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, mock_user_repository):
        """Should soft delete user successfully"""
        result = await user_service.delete_user(1)

        assert result is True
        mock_user_repository.remove_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_service, mock_user_repository):
        """Should raise error if user not found"""
        mock_user_repository.remove_by_id.return_value = False

        with pytest.raises(NotFoundException) as exc_info:
            await user_service.delete_user(999)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_restore_user_success(self, user_service, mock_user_repository, sample_user):
        """Should restore deleted user successfully"""
        result = await user_service.restore_user(1)

        assert result == sample_user
        mock_user_repository.restore_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_restore_user_not_found(self, user_service, mock_user_repository):
        """Should raise error if user not found or not deleted"""
        mock_user_repository.restore_by_id.return_value = None

        with pytest.raises(NotFoundException) as exc_info:
            await user_service.restore_user(999)

        assert exc_info.value.status_code == 404


class TestUserServiceDeletedUsers:
    """Tests for getting deleted users"""

    @pytest.mark.asyncio
    async def test_get_deleted_users(self, user_service, mock_user_repository, sample_users):
        """Should get paginated deleted user list"""
        users, total = await user_service.get_deleted_users(current=1, pageSize=10)

        assert len(users) == len(sample_users)
        assert total == len(sample_users)
        mock_user_repository.find_deleted.assert_called_once_with(1, 10)

    @pytest.mark.asyncio
    async def test_get_deleted_users_with_pagination(
        self, user_service, mock_user_repository, sample_users
    ):
        """Should get deleted users with custom pagination"""
        users, total = await user_service.get_deleted_users(current=2, pageSize=5)

        assert len(users) == len(sample_users)
        mock_user_repository.find_deleted.assert_called_once_with(2, 5)


class TestUserServiceCache:
    """Tests for cache behavior"""

    @pytest.mark.asyncio
    async def test_create_user_clears_list_cache(self, user_service):
        """Should clear list cache after creating user"""
        from unittest.mock import patch

        user_data = UserCreate(username="newuser", email="new@example.com", password="password123")

        with patch("fastapi_cache.FastAPICache.clear") as mock_clear:
            await user_service.create_user(user_data)
            mock_clear.assert_called_once_with(namespace="user_list")

    @pytest.mark.asyncio
    async def test_update_user_clears_cache(self, user_service):
        """Should clear user cache after update"""
        from unittest.mock import patch

        update_data = UserUpdate(username="updated")

        with patch("fastapi_cache.FastAPICache.clear") as mock_clear:
            await user_service.update_user(1, update_data)
            assert mock_clear.call_count == 2  # Clear user detail and list cache

    @pytest.mark.asyncio
    async def test_delete_user_clears_cache(self, user_service):
        """Should clear user cache after delete"""
        from unittest.mock import patch

        with patch("fastapi_cache.FastAPICache.clear") as mock_clear:
            await user_service.delete_user(1)
            assert mock_clear.call_count == 2  # Clear user detail and list cache
