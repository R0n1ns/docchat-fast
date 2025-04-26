from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshToken(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[datetime] = None
    type: Optional[str] = None


class TokenInDB(BaseModel):
    id: int
    token: str
    user_id: int
    is_valid: bool
    created_at: datetime
    expires_at: datetime

    class Config:
        orm_mode = True
