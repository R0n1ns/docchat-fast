from datetime import datetime
from typing import Optional, List, Any, Dict

from pydantic import BaseModel


# Document version schemas
class DocumentVersionBase(BaseModel):
    filename: str
    content_type: str


class DocumentVersionCreate(DocumentVersionBase):
    file_size: int
    storage_path: str
    nonce: str
    file_hash: str
    prev_hash: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentVersionInDB(DocumentVersionBase):
    id: int
    document_id: int
    user_id: int
    version_number: int
    file_size: int
    storage_path: str
    nonce: str
    file_hash: str
    prev_hash: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        orm_mode = True


# Document schemas
class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    filename: str
    content_type: str


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None
    is_deleted: Optional[bool] = None


class DocumentInDB(DocumentBase):
    id: int
    creator_id: int
    current_version_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        orm_mode = True


class DocumentWithVersions(DocumentInDB):
    versions: List[DocumentVersionInDB] = []


# Filter for document list
class DocumentListFilter(BaseModel):
    title: Optional[str] = None
    creator_id: Optional[int] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


class DocumentAccessBase(BaseModel):
    user_id: int
    access_level: str


class DocumentAccessCreate(DocumentAccessBase):
    pass


class DocumentAccessInDB(DocumentAccessBase):
    id: int
    document_id: int

    class Config:
        orm_mode = True
