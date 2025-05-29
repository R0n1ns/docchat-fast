from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.document import Document, DocumentVersion, DocumentAccess
from app.models.group import UserGroupMember
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentListFilter, DocumentVersionCreate


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    async def create_with_version(
        self,
        db: AsyncSession,
        *,
        obj_in: DocumentCreate,
        version_in: DocumentVersionCreate,
        creator_id: int
    ) -> Document:
        """
        Create a document with its first version.
        """
        db_obj = Document(
            title=obj_in.title,
            description=obj_in.description,
            filename=obj_in.filename,
            content_type=obj_in.content_type,
            creator_id=creator_id
        )
        db.add(db_obj)
        await db.flush()
        
        # Create first version
        version_obj = DocumentVersion(
            document_id=db_obj.id,
            user_id=creator_id,
            version_number=1,
            filename=version_in.filename,
            content_type=version_in.content_type,
            file_size=version_in.file_size,
            storage_path=version_in.storage_path,
            nonce=version_in.nonce,
            file_hash=version_in.file_hash,
            prev_hash=version_in.prev_hash,
        )
        db.add(version_obj)
        await db.flush()
        
        # Update document with current version id
        db_obj.current_version_id = version_obj.id
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj
    
    async def add_version(
        self,
        db: AsyncSession,
        *,
        document_id: int,
        version_in: DocumentVersionCreate,
        user_id: int
    ) -> Document:
        """
        Add a new version to an existing document.
        """
        document = await self.get_active(db, id=document_id)
        if not document:
            return None

        
        # Get latest version number
        result = await db.execute(
            select(DocumentVersion.version_number)
            .filter(DocumentVersion.document_id == document_id)
            .order_by(desc(DocumentVersion.version_number))
            .limit(1)
        )
        latest_version = result.scalar_one_or_none() or 0
        
        # Create new version
        version_obj = DocumentVersion(
            document_id=document_id,
            user_id=user_id,
            version_number=latest_version + 1,
            filename=version_in.filename,
            content_type=version_in.content_type,
            file_size=version_in.file_size,
            storage_path=version_in.storage_path,
            nonce=version_in.nonce,
            file_hash=version_in.file_hash,
            prev_hash=version_in.prev_hash,
        )
        db.add(version_obj)
        await db.flush()
        
        # Update document with current version id
        document.current_version_id = version_obj.id
        document.filename = version_in.filename
        document.content_type = version_in.content_type
        
        await db.commit()
        await db.refresh(document)
        
        return document
    
    async def get_with_versions(
        self,
        db: AsyncSession,
        *,
        document_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a document with all its versions.
        """
        document = await self.get_active(db, id=document_id)
        if not document:
            return None
        # Get document
        result = await db.execute(select(Document).filter(Document.id == document_id))
        document = result.scalars().first()
        if not document:
            return None
        
        # Get all versions
        result = await db.execute(
            select(DocumentVersion)
            .filter(DocumentVersion.document_id == document_id)
            .order_by(desc(DocumentVersion.version_number))
        )
        versions = result.scalars().all()
        
        return {
            "document": document,
            "versions": versions
        }
    
    async def get_version(
        self,
        db: AsyncSession,
        *,
        version_id: int
    ) -> Optional[DocumentVersion]:
        """
        Get a specific document version.
        """

        result = await db.execute(select(DocumentVersion).filter(DocumentVersion.id == version_id))
        return result.scalars().first()

    async def search_documents(
            self,
            db: AsyncSession,
            *,
            filters: DocumentListFilter,
            user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[Document]:
        # Получаем группы пользователя
        user_groups = select(UserGroupMember.group_id).where(UserGroupMember.user_id == user_id)

        query = select(Document).filter(
            Document.is_deleted == False,
            or_(
                Document.creator_id == user_id,
                Document.id.in_(
                    select(DocumentAccess.document_id).where(
                        or_(
                            DocumentAccess.user_id == user_id,
                            DocumentAccess.group_id.in_(user_groups)
                        )
                    )
                )
            )
        )
        
        # Apply filters
        if filters.title:
            query = query.filter(Document.title.ilike(f"%{filters.title}%"))
        
        if filters.creator_id:
            query = query.filter(Document.creator_id == filters.creator_id)
        
        # Apply sorting
        if filters.sort_order.lower() == "asc":
            query = query.order_by(asc(getattr(Document, filters.sort_by)))
        else:
            query = query.order_by(desc(getattr(Document, filters.sort_by)))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_active(self, db: AsyncSession, *, id: int) -> Optional[Document]:
        """Получить неудалённый документ по ID."""
        result = await db.execute(
            select(Document)
            .filter(Document.id == id, Document.is_deleted == False)
        )
        return result.scalars().first()

    async def mark_as_deleted(
            self,
            db: AsyncSession,
            *,
            document_id: int
    ) -> Optional[Document]:
        # Изменено: помечаем только активные документы
        document = await self.get_active(db, id=document_id)
        if not document:
            return None

        document.is_deleted = True
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document

    async def grant_group_access(
            self,
            db: AsyncSession,
            document_id: int,
            group_id: int,
            access_level: str = 'read'
    ) -> DocumentAccess:
        access = DocumentAccess(
            document_id=document_id,
            group_id=group_id,
            access_level=access_level
        )
        db.add(access)
        await db.commit()
        return access

    async def revoke_group_access(
            self,
            db: AsyncSession,
            document_id: int,
            group_id: int
    ) -> bool:
        result = await db.execute(
            select(DocumentAccess)
            .filter(DocumentAccess.document_id == document_id)
            .filter(DocumentAccess.group_id == group_id)
        )
        access = result.scalars().first()
        if access:
            await db.delete(access)
            await db.commit()
            return True
        return False

document_crud = CRUDDocument(Document)
