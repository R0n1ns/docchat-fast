from typing import Any, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util import greenlet_spawn

from app.api.dependencies import get_db, get_current_active_user, get_current_active_manager, get_current_active_admin
from app.crud.crud_document import document_crud
from app.crud.crud_document_access import document_access_crud
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentInDB, DocumentListFilter, DocumentAccessCreate, \
    DocumentAccessInDB
from app.services.document import create_document, get_document_by_id, update_document, remove_document, search_documents, verify_document_integrity
from app.services.minio import get_document_file

router = APIRouter()

@router.post("", response_model=DocumentInDB)
async def create_new_document(
    *,
    db: AsyncSession = Depends(get_db),
    title: str,
    description: Optional[str] = None,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new document.
    """
    document_in = DocumentCreate(
        title=title,
        description=description,
        filename=file.filename,
        content_type=file.content_type
    )
    document = await create_document(
        db=db, 
        obj_in=document_in, 
        file=file,
        creator_id=current_user.id
    )
    return document

@router.get("", response_model=List[DocumentInDB])
async def read_documents(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    title: Optional[str] = None,
    creator_id: Optional[int] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve documents.
    """
    filters = DocumentListFilter(
        title=title,
        creator_id=creator_id,
        sort_by=sort_by,
        sort_order=sort_order
    )
    # Regular users can only see their own documents
    # Managers and admins can see all documents
    if current_user.role == "user":
        filters.creator_id = current_user.id
        
    documents = await search_documents(
        db=db,
        filters=filters,
        skip=skip,
        limit=limit,
        user_id=current_user.id
    )
    return documents

@router.get("/{document_id}", response_model=DocumentInDB)
async def read_document(
    *,
    db: AsyncSession = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get document by ID.
    """
    document = await get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check if user has access to this document
    if current_user.role == "user" and document.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this document",
        )
        
    return document

@router.get("/{document_id}/download")
async def download_document(
    *,
    db: AsyncSession = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Download document file.
    """
    document = await get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check if user has access to this document
    has_access = (
            document.creator_id == current_user.id or
            await greenlet_spawn(lambda: any(access.user_id == current_user.id for access in document.access_list))
    )

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this document",
        )
    
    # Get file from MinIO
    try:
        file_obj = await get_document_file(document_id=document_id, version_id=document.current_version_id)
        filename = document.filename
        # Return file as streaming response
        return StreamingResponse(
            file_obj,
            media_type=document.content_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document file: {str(e)}",
        )

@router.patch("/{document_id}", response_model=DocumentInDB)
async def update_document_info(
    *,
    db: AsyncSession = Depends(get_db),
    document_id: int,
    document_in: DocumentUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update document information.
    """
    document = await get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check if user has access to update this document
    if current_user.role == "user" and document.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this document",
        )
    
    document = await update_document(
        db=db, 
        document_id=document_id, 
        obj_in=document_in,
        user_id=current_user.id
    )
    return document

@router.post("/{document_id}/upload", response_model=DocumentInDB)
async def upload_new_version(
    *,
    db: AsyncSession = Depends(get_db),
    document_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Upload a new version of an existing document.
    """
    document = await get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check if user has access to update this document
    if current_user.role == "user" and document.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this document",
        )
    
    # Update document with new file
    document_update = DocumentUpdate(
        filename=file.filename,
        content_type=file.content_type
    )
    
    document = await update_document(
        db=db, 
        document_id=document_id, 
        obj_in=document_update,
        file=file,
        user_id=current_user.id
    )
    return document

@router.delete("/{document_id}", response_model=DocumentInDB)
async def delete_document(
    *,
    db: AsyncSession = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a document.
    """
    document = await get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check if user has access to delete this document
    if current_user.role == "user" and document.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this document",
        )
    
    document = await remove_document(db=db, document_id=document_id)
    return document

@router.get("/{document_id}/verify", status_code=status.HTTP_200_OK)
async def verify_integrity(
    *,
    db: AsyncSession = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Verify document integrity using the hash chain.
    """
    document = await get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check if user has access to this document
    if current_user.role == "user" and document.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this document",
        )
    
    # Verify document integrity
    is_valid, message = await verify_document_integrity(db=db, document_id=document_id)
    
    return {
        "is_valid": is_valid,
        "message": message
    }


@router.post("/{document_id}/share", status_code=status.HTTP_201_CREATED)
async def share_document(
        *,
        db: AsyncSession = Depends(get_db),
        document_id: int,
        access_in: DocumentAccessCreate,
        current_user: User = Depends(get_current_active_user),
):
    document = await get_document_by_id(db, document_id)
    if document.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can share documents")

    return await document_access_crud.grant_access(
        db,
        document_id=document_id,
        user_id=access_in.user_id,
        access_level=access_in.access_level
    )


@router.delete("/{document_id}/share/{user_id}")
async def revoke_access(
        *,
        db: AsyncSession = Depends(get_db),
        document_id: int,
        access_in: DocumentAccessCreate,
        current_user: User = Depends(get_current_active_user)):
    # Аналогичная проверка прав
    await document_access_crud.revoke_access(db, document_id=document_id, user_id=current_user.id)
    return {"status": "success"}


@router.get("/{document_id}/access_list")
async def get_my_accessible_documents(
        *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Получить все документы, к которым у текущего пользователя есть доступ
    """
    # Получаем все документы, где пользователь имеет доступ
    accessible_documents = await document_access_crud.get_user_accessible_documents(
        db, user_id=current_user.id
    )
    return accessible_documents
