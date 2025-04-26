import os
import base64
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Union, Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import current_app
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

# Constants
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
SECRET_KEY = os.environ.get("SECRET_KEY", "secure-document-management-key")
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "a-32-byte-string-for-aes-encryption!").encode()

# Token functions
def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new refresh token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def decode_token(token: str) -> Dict:
    """
    Decode a JWT token
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None

# Password functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    """
    return check_password_hash(hashed_password, plain_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password
    """
    return generate_password_hash(password)

# File encryption functions
def encrypt_file(file_content: bytes) -> tuple[bytes, bytes]:
    """
    Encrypts file content using AES-256-GCM.
    Returns (encrypted_content, nonce)
    """
    # Generate a random 96-bit nonce (12 bytes)
    nonce = os.urandom(12)
    
    # Create an encryptor
    aesgcm = AESGCM(ENCRYPTION_KEY)
    
    # Encrypt the data
    encrypted_content = aesgcm.encrypt(nonce, file_content, None)
    
    return encrypted_content, nonce

def decrypt_file(encrypted_content: bytes, nonce: bytes) -> bytes:
    """
    Decrypts file content using AES-256-GCM.
    """
    # Create a decryptor
    aesgcm = AESGCM(ENCRYPTION_KEY)
    
    # Decrypt the data
    decrypted_content = aesgcm.decrypt(nonce, encrypted_content, None)
    
    return decrypted_content