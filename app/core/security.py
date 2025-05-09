from datetime import datetime, timedelta
from typing import Any, Optional, Union
import os

from jose import jwt
from passlib.context import CryptContext
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def encrypt_file(file_content: bytes) -> tuple[bytes, bytes]:
    """
    Encrypts file content using AES-256-GCM.
    Returns (encrypted_content, nonce)
    """
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    # print(settings.ENCRYPTION_KEY)
    # print(len(settings.ENCRYPTION_KEY))
    aesgcm = AESGCM(settings.ENCRYPTION_KEY)
    encrypted_content = aesgcm.encrypt(nonce, file_content, None)
    return encrypted_content, nonce

def decrypt_file(encrypted_content: bytes, nonce: bytes) -> bytes:
    """
    Decrypts file content using AES-256-GCM.
    """
    # print(settings.ENCRYPTION_KEY)
    # print(len(settings.ENCRYPTION_KEY))
    aesgcm = AESGCM(settings.ENCRYPTION_KEY)
    decrypted_content = aesgcm.decrypt(nonce, encrypted_content, None)
    return decrypted_content
