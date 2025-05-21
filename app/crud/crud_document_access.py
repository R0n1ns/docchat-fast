from typing import List, Any, Coroutine, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.document import DocumentAccess, Document
from app.schemas.document import DocumentAccessCreate

class CRUDDocumentAccess:
    async def grant_access(
        self, db: AsyncSession, *, document_id: int, user_id: int, access_level: str
    ) -> DocumentAccess:
        access = DocumentAccess(
            document_id=document_id,
            user_id=user_id,
            access_level=access_level
        )
        db.add(access)
        await db.commit()
        await db.refresh(access)
        return access

    async def revoke_access(
        self, db: AsyncSession, *, document_id: int, user_id: int
    ) -> None:
        await db.execute(
            delete(DocumentAccess)
            .where(DocumentAccess.document_id == document_id)
            .where(DocumentAccess.user_id == user_id)
        )
        await db.commit()

    async def get_user_accessible_documents(
            self, db: AsyncSession, user_id: int
    ) -> list[Any] | Sequence[Document]:
        # Получаем все записи доступа пользователя
        result = await db.execute(
            select(DocumentAccess.document_id)
            .filter(DocumentAccess.user_id == user_id)
        )
        document_ids = result.scalars().all()

        # Получаем документы по найденным ID
        if not document_ids:
            return []

        result = await db.execute(
            select(Document)
            .filter(Document.id.in_(document_ids))
        )
        return result.scalars().all()

document_access_crud = CRUDDocumentAccess()