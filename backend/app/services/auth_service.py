"""
Authentication Service
"""

import logging
from datetime import datetime, timezone

from jose import JWTError, jwt

from app.core.config import settings
from app.core.redis import redis_client
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.exceptions.base import UnauthorizedException
from app.models.user import User
from app.repository.user_repository import UserRepository
from app.schemas.token import Token

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def _blacklist_token(self, jti: str, exp: int) -> None:
        """Add JTI to Redis blacklist until expiration"""
        if redis_client:
            now = datetime.now(timezone.utc).timestamp()
            ttl = int(exp - now)
            if ttl > 0:
                await redis_client.set(f"blacklist:{jti}", "revoked", ex=ttl)
                logger.debug(f"Token {jti} blacklisted for {ttl} seconds")

    async def _is_token_blacklisted(self, jti: str) -> bool:
        """Check if JTI is in Redis blacklist"""
        if redis_client:
            exists = await redis_client.get(f"blacklist:{jti}")
            return exists is not None
        return False

    async def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate user by username and password"""
        # Try finding by username first
        user = await self.user_repo.find_by_username(username)

        # If not found, try finding by email
        if not user:
            user = await self.user_repo.find_by_email(username)

        if not user:
            raise UnauthorizedException("Incorrect username or password")

        # Verify password
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Incorrect username or password")

        # Check active
        if not user.is_active:
            raise UnauthorizedException("User is inactive")

        return user

    async def login(self, username: str, password: str) -> Token:
        """Login user and return token pair"""
        user = await self.authenticate_user(username, password)

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    async def refresh_token(self, refresh_token: str) -> Token:
        """Use refresh token to get new token pair (Rotation)"""
        try:
            payload = jwt.decode(
                refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )

            token_type = payload.get("type")
            if token_type != "refresh":
                raise UnauthorizedException("Invalid token type")

            jti = payload.get("jti")
            user_id = payload.get("sub")
            exp = payload.get("exp")

            if not jti or not user_id or not exp:
                raise UnauthorizedException("Invalid token payload")

            # Check blacklist
            if await self._is_token_blacklisted(jti):
                raise UnauthorizedException("Token has been revoked")

            # Check user existence
            user = await self.user_repo.find_by_id(int(user_id))
            if not user or not user.is_active:
                raise UnauthorizedException("User no longer exists or is inactive")

            # Rotate: Blacklist the used refresh token
            await self._blacklist_token(jti, exp)

            # Issue new pair
            new_access_token = create_access_token(subject=user.id)
            new_refresh_token = create_refresh_token(subject=user.id)

            return Token(
                access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer"
            )

        except JWTError:
            raise UnauthorizedException("Invalid refresh token")

    async def logout(self, access_token: str) -> None:
        """Logout: Blacklist the valid access token"""
        try:
            payload = jwt.decode(
                access_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            jti = payload.get("jti")
            exp = payload.get("exp")

            if jti and exp:
                await self._blacklist_token(jti, exp)

        except JWTError:
            # If token is invalid, just ignore
            pass

    async def validate_access_token(self, token: str) -> User:
        """Validate access token and return user"""
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )

            token_type = payload.get("type")
            if token_type != "access":
                raise UnauthorizedException("Invalid token type")

            jti = payload.get("jti")
            user_id = payload.get("sub")

            if not jti or not user_id:
                raise UnauthorizedException("Invalid token payload")

            # Check blacklist
            if await self._is_token_blacklisted(jti):
                raise UnauthorizedException("Token has been revoked")

            # Get user
            user = await self.user_repo.find_by_id(int(user_id))
            if not user or not user.is_active:
                raise UnauthorizedException("User no longer exists or is inactive")

            return user

        except JWTError:
            raise UnauthorizedException("Could not validate credentials")
