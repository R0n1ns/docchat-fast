import pyotp
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user_crud
from app.crud.crud_token import token_crud
from app.models.user import User
from app.services.email import send_email

# In-memory storage for TOTP secrets (in production, this should be stored in Redis or similar)
# This is a simple implementation for demonstration purposes
totp_secrets = {}

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.
    """
    return await user_crud.authenticate(db, email=email, password=password)

async def verify_refresh_token(db: AsyncSession, token: str) -> Optional[int]:
    """
    Verify if refresh token is valid and return user_id if it is.
    """
    db_token = await token_crud.get_by_token(db, token=token)
    if not db_token or not db_token.is_valid or db_token.expires_at < datetime.now(timezone.utc):
        return None
    return db_token.user_id

async def generate_totp_secret(email: str) -> str:
    """
    Generate a TOTP secret for a user.
    """
    secret = pyotp.random_base32()
    totp_secrets[email] = {
        "secret": secret,
        "created_at": datetime.utcnow()
    }
    return secret

async def get_totp_secret(email: str) -> Optional[str]:
    """
    Get the TOTP secret for a user.
    """
    if email not in totp_secrets:
        return None
    
    # Check if TOTP secret is expired (5 minutes)
    created_at = totp_secrets[email]["created_at"]
    if datetime.utcnow() - created_at > timedelta(minutes=5):
        del totp_secrets[email]
        return None
        
    return totp_secrets[email]["secret"]

async def generate_totp_code(email: str) -> Tuple[str, str]:
    """
    Generate a TOTP code for a user.
    Returns the code and the secret.
    """
    secret = await generate_totp_secret(email)
    totp = pyotp.TOTP(secret, digits=settings.TOTP_DIGITS, interval=settings.TOTP_INTERVAL)
    return totp.now(), secret

async def verify_totp(email: str, code: str) -> bool:
    """
    Verify a TOTP code for a user.
    """
    secret = await get_totp_secret(email)
    if not secret:
        return False
    
    totp = pyotp.TOTP(secret, digits=settings.TOTP_DIGITS, interval=settings.TOTP_INTERVAL)
    return totp.verify(code)

async def send_totp_code(email: str) -> bool:
    """
    Generate and send a TOTP code to the user's email.
    """
    code, _ = await generate_totp_code(email)
    
    # Send email with the code
    subject = f"{settings.PROJECT_NAME} - Your Authentication Code"
    message = f"""
    <h1>Authentication Code</h1>
    <p>Your authentication code is: <strong>{code}</strong></p>
    <p>This code will expire in {settings.TOTP_INTERVAL} seconds.</p>
    <p>If you did not request this code, please ignore this email.</p>
    """
    
    return await send_email(
        email_to=email,
        subject_template=subject,
        html_template=message
    )
