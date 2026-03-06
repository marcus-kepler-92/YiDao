"""
Test utilities and helpers
"""

from datetime import datetime
from unittest.mock import MagicMock


def create_mock_user(
    id: int = 1,
    username: str = "testuser",
    email: str = "test@example.com",
    is_active: bool = True,
    is_deleted: bool = False,
    **kwargs,
) -> MagicMock:
    """
    Create a mock User object with default values.

    Args:
        id: User ID
        username: Username
        email: Email address
        is_active: Active status
        is_deleted: Deleted status
        **kwargs: Additional attributes to set

    Returns:
        MagicMock configured as a User object
    """
    user = MagicMock()
    user.id = id
    user.username = username
    user.email = email
    user.hashed_password = f"hashed_password_{id}"
    user.is_active = is_active
    user.is_deleted = is_deleted
    user.deleted_at = datetime.now() if is_deleted else None
    user.created_at = datetime(2024, 1, 1, 0, 0, 0)
    user.updated_at = datetime(2024, 1, 1, 0, 0, 0)

    for key, value in kwargs.items():
        setattr(user, key, value)

    return user


def create_mock_users(count: int = 3, **kwargs) -> list[MagicMock]:
    """
    Create a list of mock User objects.

    Args:
        count: Number of users to create
        **kwargs: Additional attributes to set on all users

    Returns:
        List of MagicMock User objects
    """
    return [
        create_mock_user(
            id=i + 1, username=f"user{i + 1}", email=f"user{i + 1}@example.com", **kwargs
        )
        for i in range(count)
    ]


class ResponseAssertions:
    """Helper class for common response assertions"""

    @staticmethod
    def assert_success_response(response_data: dict, message: str | None = None):
        """Assert response indicates success"""
        assert response_data["success"] is True
        if message:
            assert response_data["message"] == message

    @staticmethod
    def assert_error_response(response_data: dict, message: str | None = None):
        """Assert response indicates error"""
        assert response_data["success"] is False
        if message:
            assert message in response_data["message"]

    @staticmethod
    def assert_paginated_response(response_data: dict):
        """Assert response is a valid paginated response"""
        assert response_data["success"] is True
        assert "data" in response_data
        data = response_data["data"]
        assert "list" in data
        assert "total" in data
        assert "current" in data
        assert "pageSize" in data
        assert isinstance(data["list"], list)
        assert isinstance(data["total"], int)


def assert_called_with_any(mock: MagicMock, **expected_kwargs):
    """
    Assert mock was called with at least the expected kwargs.
    Useful when you don't care about all arguments.
    """
    mock.assert_called()
    call_kwargs = mock.call_args.kwargs if mock.call_args.kwargs else {}

    for key, value in expected_kwargs.items():
        assert key in call_kwargs, f"Expected kwarg '{key}' not found in call"
        assert call_kwargs[key] == value, f"Expected {key}={value}, got {call_kwargs[key]}"
