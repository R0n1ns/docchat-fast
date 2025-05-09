import hashlib
import uuid
from typing import Optional, List, Tuple, Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_document import document_crud
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentVersionCreate, DocumentListFilter
from app.services.minio import upload_file

async def create_document(
    db: AsyncSession,
    obj_in: DocumentCreate,
    file: UploadFile,
    creator_id: int
) -> Document:
    """
    Create a new document with the first version.
    """
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Generate unique storage path
    storage_path = f"documents/{creator_id}/{uuid.uuid4()}".replace("-", "")
    
    # Upload file to MinIO
    object_path, nonce, file_hash = await upload_file(file_content, storage_path)
    
    # Create version
    version_in = DocumentVersionCreate(
        filename=obj_in.filename,
        content_type=obj_in.content_type,
        file_size=file_size,
        storage_path=object_path,
        nonce=nonce,
        file_hash=file_hash,
        prev_hash=None,  # First version, no previous hash
        metadata={"original_name": file.filename}
    )
    
    # Create document with version
    return await document_crud.create_with_version(
        db=db,
        obj_in=obj_in,
        version_in=version_in,
        creator_id=creator_id
    )

async def get_document_by_id(
    db: AsyncSession,
    document_id: int
) -> Optional[Document]:
    """
    Get a document by ID.
    """
    return await document_crud.get(db, id=document_id)

async def update_document(
    db: AsyncSession,
    document_id: int,
    obj_in: DocumentUpdate,
    user_id: int,
    file: Optional[UploadFile] = None
) -> Optional[Document]:
    """
    Update a document. If file is provided, create a new version.
    """
    # Get document
    document = await document_crud.get(db, id=document_id)
    if not document:
        return None
    
    # If file is provided, create a new version
    if file:
        # Get current version for prev_hash
        current_version = await document_crud.get_version(db, version_id=document.current_version_id)
        if not current_version:
            return None
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Generate unique storage path
        storage_path = f"documents/{user_id}/{uuid.uuid4()}"
        
        # Upload file to MinIO
        object_path, nonce, file_hash = await upload_file(file_content, storage_path)
        
        # Create version
        version_in = DocumentVersionCreate(
            filename=file.filename,
            content_type=file.content_type,
            file_size=file_size,
            storage_path=object_path,
            nonce=nonce,
            file_hash=file_hash,
            prev_hash=current_version.file_hash,  # Link to previous version
            metadata={"original_name": file.filename}
        )
        
        # Add version to document
        document = await document_crud.add_version(
            db=db,
            document_id=document_id,
            version_in=version_in,
            user_id=user_id
        )
    
    # Update document metadata
    if obj_in.title is not None or obj_in.description is not None or obj_in.is_deleted is not None:
        document = await document_crud.update(db, db_obj=document, obj_in=obj_in)
    
    return document

async def remove_document(
    db: AsyncSession,
    document_id: int
) -> Optional[Document]:
    """
    Soft delete a document (mark as deleted).
    """
    return await document_crud.mark_as_deleted(db, document_id=document_id)

async def search_documents(
    db: AsyncSession,
    filters: DocumentListFilter,
    skip: int = 0,
    limit: int = 100
) -> List[Document]:
    """
    Search for documents based on filters.
    """
    return await document_crud.search_documents(
        db=db,
        filters=filters,
        skip=skip,
        limit=limit
    )

async def verify_document_integrity(
    db: AsyncSession,
    document_id: int
) -> Tuple[bool, str]:
    """
    Verify the integrity of a document by checking the hash chain.
    """
    # Get document with all versions
    doc_with_versions = await document_crud.get_with_versions(db, document_id=document_id)
    if not doc_with_versions:
        return False, "Document not found"
    
    versions = doc_with_versions["versions"]
    if not versions:
        return False, "Document has no versions"
    
    # Verify the hash chain - versions are ordered by version_number desc
    versions.reverse()  # Reverse to get chronological order
    
    # Check first version has no prev_hash
    if versions[0].prev_hash is not None:
        return False, "First version has a previous hash set, which is invalid"
    
    # Check all subsequent versions
    for i in range(1, len(versions)):
        if versions[i].prev_hash != versions[i-1].file_hash:
            return False, f"Hash chain broken at version {versions[i].version_number}"
    
    return True, "Document integrity verified"
