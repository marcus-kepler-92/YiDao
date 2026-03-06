"""
Authentication API
"""

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import get_auth_service, get_current_user, oauth2_scheme
from app.models.user import User
from app.schemas.auth import RefreshTokenRequest
from app.schemas.common import Response
from app.schemas.token import Token
from app.schemas.user import UserResponse as UserSchema
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Response[Token])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    token = await service.login(form_data.username, form_data.password)
    return Response(data=token, message="Login successful")


@router.post("/refresh", response_model=Response[Token])
async def refresh(
    request: RefreshTokenRequest, service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    Refresh access token
    """
    token = await service.refresh_token(request.refresh_token)
    return Response(data=token, message="Token refreshed")


@router.post("/logout", response_model=Response[None])
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    Logout current user
    """
    await service.logout(token)
    return Response(data=None, message="Logout successful")


@router.get("/me", response_model=Response[UserSchema])
async def read_users_me(current_user: User = Depends(get_current_user)) -> Any:
    """
    Get current user details
    """
    return Response(data=current_user)
