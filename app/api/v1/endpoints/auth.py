from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.crud.crud_token import token_crud
from app.crud.crud_user import user_crud
from app.models.user import User
from app.schemas.token import Token, RefreshToken
from app.schemas.user import UserCreate, UserInDB
from app.services.auth import authenticate_user, verify_refresh_token, send_totp_code, verify_totp

router = APIRouter()

@router.post("/register", response_model=UserInDB)
async def register_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate
) -> Any:
    """
    Register a new user.
    """
    # Check if user already exists
    user = await user_crud.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system",
        )
    
    # Create user
    user = await user_crud.create(db, obj_in=user_in)
    return user

@router.post("/login-init", status_code=status.HTTP_200_OK)
async def login_init(
    *,
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Step 1: Validate username/password and send TOTP code.
    """
    user = await authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate and send TOTP code via email
    await send_totp_code(user.email)
    
    return {"msg": "TOTP code has been sent to your email", "email": user.email}

@router.post("/login", response_model=Token)
async def login_access_token(
    *,
    db: AsyncSession = Depends(get_db),
    email: str = Body(...),
    totp_code: str = Body(...),
) -> Any:
    """
    Step 2: Verify TOTP code and issue JWT tokens.
    """
    # Verify TOTP code
    is_valid = await verify_totp(email, totp_code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TOTP code",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user = await user_crud.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Create access token and refresh token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        subject=str(user.id), expires_delta=refresh_token_expires
    )
    
    # Store refresh token in database
    await token_crud.create_refresh_token(db, user_id=user.id, refresh_token=refresh_token)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    *,
    db: AsyncSession = Depends(get_db),
    refresh_token: RefreshToken
) -> Any:
    """
    Refresh access token using refresh token.
    """
    user_id = await verify_refresh_token(db, refresh_token.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token and refresh token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        subject=str(user_id), expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(
        subject=str(user_id), expires_delta=refresh_token_expires
    )
    
    # Update refresh token in database
    await token_crud.update_refresh_token(
        db, 
        user_id=user_id,
        old_refresh_token=refresh_token.refresh_token,
        new_refresh_token=new_refresh_token
    )
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    refresh_token: RefreshToken
) -> Any:
    """
    Logout user by invalidating refresh token.
    """
    await token_crud.invalidate_refresh_token(
        db, user_id=current_user.id, refresh_token=refresh_token.refresh_token
    )
    return {"msg": "Successfully logged out"}
