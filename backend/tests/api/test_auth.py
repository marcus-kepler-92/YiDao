from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import settings

# Use api marker for all tests in this file
pytestmark = pytest.mark.api


@pytest.fixture
def mock_verify_password():
    with patch("app.services.auth_service.verify_password") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_redis_client():
    with patch("app.services.auth_service.redis_client", new_callable=AsyncMock) as mock:
        mock.get.return_value = None
        mock.set.return_value = True
        yield mock


def test_login_success(
    client_with_mocked_service,
    mock_user_repository,
    sample_user,
    mock_verify_password,
    mock_redis_client,
):
    """Test successful login returns token pair"""
    # Setup mock
    mock_user_repository.find_by_username.return_value = sample_user

    # Execute
    response = client_with_mocked_service.post(
        f"{settings.api_prefix_v1}/auth/login",
        data={"username": sample_user.username, "password": "password123"},
    )

    # Verify
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure(client_with_mocked_service, mock_user_repository, mock_redis_client):
    """Test login with invalid credentials returns 401"""
    # Setup mock to return None (user not found)
    mock_user_repository.find_by_username.return_value = None
    mock_user_repository.find_by_email.return_value = None

    # Execute
    response = client_with_mocked_service.post(
        f"{settings.api_prefix_v1}/auth/login",
        data={"username": "wronguser", "password": "wrongpassword"},
    )

    # Verify
    assert response.status_code == 401


def test_login_wrong_password(
    client_with_mocked_service, mock_user_repository, sample_user, mock_redis_client
):
    """Test login with wrong password returns 401"""
    # Setup mock
    mock_user_repository.find_by_username.return_value = sample_user

    # Patch verify_password to return False
    with patch("app.services.auth_service.verify_password", return_value=False):
        # Execute
        response = client_with_mocked_service.post(
            f"{settings.api_prefix_v1}/auth/login",
            data={"username": sample_user.username, "password": "wrongpassword"},
        )

    # Verify
    assert response.status_code == 401


def test_access_token_validity(
    client_with_mocked_service,
    mock_user_repository,
    sample_user,
    mock_verify_password,
    mock_redis_client,
):
    """Test access token can assess protected route"""
    # 1. Login to get token
    mock_user_repository.find_by_username.return_value = sample_user
    login_res = client_with_mocked_service.post(
        f"{settings.api_prefix_v1}/auth/login",
        data={"username": sample_user.username, "password": "password123"},
    )
    access_token = login_res.json()["data"]["access_token"]

    # 2. Access protected route
    # Mock find_by_id for the token validation
    mock_user_repository.find_by_id.return_value = sample_user

    response = client_with_mocked_service.get(
        f"{settings.api_prefix_v1}/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assert response.json()["data"]["username"] == sample_user.username


def test_refresh_token_flow(
    client_with_mocked_service,
    mock_user_repository,
    sample_user,
    mock_verify_password,
    mock_redis_client,
):
    """Test refresh token can get new token pair"""
    # 1. Login to get token
    mock_user_repository.find_by_username.return_value = sample_user
    login_res = client_with_mocked_service.post(
        f"{settings.api_prefix_v1}/auth/login",
        data={"username": sample_user.username, "password": "password123"},
    )
    refresh_token = login_res.json()["data"]["refresh_token"]

    # 2. Use refresh token
    mock_user_repository.find_by_id.return_value = sample_user

    response = client_with_mocked_service.post(
        f"{settings.api_prefix_v1}/auth/refresh", json={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["access_token"] != refresh_token


def test_logout(
    client_with_mocked_service,
    mock_user_repository,
    sample_user,
    mock_verify_password,
    mock_redis_client,
):
    """Test logout invalidates token"""
    # 1. Login
    mock_user_repository.find_by_username.return_value = sample_user
    login_res = client_with_mocked_service.post(
        f"{settings.api_prefix_v1}/auth/login",
        data={"username": sample_user.username, "password": "password123"},
    )
    access_token = login_res.json()["data"]["access_token"]

    # 2. Logout
    response = client_with_mocked_service.post(
        f"{settings.api_prefix_v1}/auth/logout", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200

    # Check if token was added to blacklist (Redis set called)
    mock_redis_client.set.assert_called()
