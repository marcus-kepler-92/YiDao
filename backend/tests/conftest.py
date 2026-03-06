"""
Pytest fixtures and configuration
"""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# =============================================================================
# Environment Setup (must be before any app imports)
# =============================================================================

os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("ENABLE_RATE_LIMIT", "false")  # Disable rate limiting in tests


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.refresh = MagicMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.query = MagicMock()
    return session


@pytest.fixture
def mock_cache():
    """Mock Redis cache service (deprecated, kept for compatibility)"""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.get_json = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.set_json = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.delete_pattern = AsyncMock(return_value=0)
    cache.exists = AsyncMock(return_value=False)
    cache.connect = AsyncMock()
    cache.disconnect = AsyncMock()
    return cache


@pytest.fixture(autouse=True)
async def init_cache():
    """Initialize FastAPICache for all tests"""
    from fastapi_cache import FastAPICache
    from fastapi_cache.backends.inmemory import InMemoryBackend

    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    yield
    # No explicit cleanup needed for InMemoryBackend in this context


# =============================================================================
# User Fixtures
# =============================================================================


@pytest.fixture
def sample_user_data():
    """Sample user creation data"""
    return {"username": "testuser", "email": "test@example.com", "password": "password123"}


@pytest.fixture
def sample_user():
    """Sample user object"""
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.hashed_password = "hashed_password123"
    user.is_active = True
    user.deleted_at = None
    user.is_deleted = False
    user.created_at = datetime(2024, 1, 1, 0, 0, 0)
    user.updated_at = datetime(2024, 1, 1, 0, 0, 0)
    return user


@pytest.fixture
def sample_users():
    """List of sample users"""
    users = []
    for i in range(3):
        user = MagicMock()
        user.id = i + 1
        user.username = f"user{i + 1}"
        user.email = f"user{i + 1}@example.com"
        user.hashed_password = f"hashed_password{i + 1}"
        user.is_active = True
        user.deleted_at = None
        user.is_deleted = False
        user.created_at = datetime(2024, 1, 1, 0, 0, 0)
        user.updated_at = datetime(2024, 1, 1, 0, 0, 0)
        users.append(user)
    return users


# =============================================================================
# Repository Fixtures
# =============================================================================


@pytest.fixture
def mock_user_repository(sample_user, sample_users):
    """Mock user repository (async)"""
    repo = MagicMock()
    repo.add = AsyncMock(return_value=sample_user)
    repo.find_by_id = AsyncMock(return_value=sample_user)
    repo.find_by_email = AsyncMock(return_value=None)
    repo.find_by_username = AsyncMock(return_value=None)
    repo.find_all = AsyncMock(return_value=sample_users)

    # Mock find_paginated to accept all query parameters
    async def mock_find_paginated(*args, **kwargs):
        return (sample_users, len(sample_users))

    repo.find_paginated = AsyncMock(side_effect=mock_find_paginated)
    repo.update_by_id = AsyncMock(return_value=sample_user)
    repo.remove_by_id = AsyncMock(return_value=True)
    repo.restore_by_id = AsyncMock(return_value=sample_user)
    repo.find_deleted = AsyncMock(return_value=(sample_users, len(sample_users)))
    return repo


# =============================================================================
# Service Fixtures
# =============================================================================


@pytest.fixture
def user_service(mock_user_repository):
    """User service with mocked dependencies"""
    from app.services.user_service import UserService

    return UserService(repo=mock_user_repository)


# =============================================================================
# Client Fixtures
# =============================================================================


@pytest.fixture
def client():
    """
    Test client for FastAPI app.
    Uses mocked dependencies to avoid requiring real DB/Redis connections.
    """
    with (
        patch("app.core.database.init_db", new_callable=AsyncMock),
        patch("app.core.database.close_db", new_callable=AsyncMock),
        patch("fastapi_cache.FastAPICache.init"),
        patch("app.core.tracing.setup_tracing"),
    ):
        from app.main import app

        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def client_with_mocked_service(mock_user_repository, mock_cache):
    """
    Test client with mocked UserService dependencies.
    Use this for API tests that need controlled service behavior.
    """
    from app.dependencies import get_user_repository

    async def override_get_user_repository():
        return mock_user_repository

    with (
        patch("app.core.database.init_db", new_callable=AsyncMock),
        patch("app.core.database.close_db", new_callable=AsyncMock),
        patch("fastapi_cache.FastAPICache.init"),
        patch("app.core.tracing.setup_tracing"),
    ):
        from app.main import app

        app.dependency_overrides[get_user_repository] = override_get_user_repository

        with TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()
