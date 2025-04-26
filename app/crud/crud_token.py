from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.core.config import settings
from app.models.token import RefreshToken


class CRUDToken(CRUDBase[RefreshToken, None, None]):
    async def get_by_token(
        self, db: AsyncSession, *, token: str
    ) -> Optional[RefreshToken]:
        """
        Get a refresh token by its value.
        """
        result = await db.execute(
            select(RefreshToken).filter(
                RefreshToken.token == token,
                RefreshToken.is_valid == True,
                RefreshToken.expires_at > datetime.utcnow()
            )
        )
        return result.scalars().first()
    
    async def create_refresh_token(
        self, db: AsyncSession, *, user_id: int, refresh_token: str
    ) -> RefreshToken:
        """
        Create a new refresh token.
        """
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        db_obj = RefreshToken(
            token=refresh_token,
            user_id=user_id,
            expires_at=expires_at,
            is_valid=True
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def invalidate_refresh_token(
        self, db: AsyncSession, *, user_id: int, refresh_token: str
    ) -> bool:
        """
        Invalidate a refresh token.
        """
        result = await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token == refresh_token,
                RefreshToken.user_id == user_id,
                RefreshToken.is_valid == True
            )
            .values(is_valid=False)
        )
        await db.commit()
        return result.rowcount > 0
    
    async def update_refresh_token(
        self, db: AsyncSession, *, user_id: int, old_refresh_token: str, new_refresh_token: str
    ) -> Optional[RefreshToken]:
        """
        Invalidate old refresh token and create a new one.
        """
        # Invalidate old token
        await self.invalidate_refresh_token(db, user_id=user_id, refresh_token=old_refresh_token)
        
        # Create new token
        return await self.create_refresh_token(db, user_id=user_id, refresh_token=new_refresh_token)
    
    async def invalidate_all_user_tokens(
        self, db: AsyncSession, *, user_id: int
    ) -> bool:
        """
        Invalidate all refresh tokens for a user.
        """
        result = await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_valid == True
            )
            .values(is_valid=False)
        )
        await db.commit()
        return result.rowcount > 0


token_crud = CRUDToken(RefreshToken)
