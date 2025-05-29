from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.schemas.document import DocumentBase
from app.schemas.user import User


class UserGroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    leader_id: Optional[int] = None

class UserGroupCreate(UserGroupBase):
    pass

class UserGroupUpdate(UserGroupBase):
    pass

class UserGroupInDB(UserGroupBase):
    id: int
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = None

    class Config:
        orm_mode = True

class UserGroupMemberBase(BaseModel):
    user_id: int
    group_id: int

class UserGroupMemberCreate(UserGroupMemberBase):
    pass

class UserGroupMemberInDB(UserGroupMemberBase):
    joined_at: datetime

    class Config:
        orm_mode = True


class DocumentGroupAccessBase(BaseModel):
    group_id: int
    access_level: str  # read/write


class DocumentGroupAccessCreate(DocumentGroupAccessBase):
    pass


class DocumentGroupAccessInDB(DocumentGroupAccessBase):
    id: int
    document_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# Обновим DocumentAccessBase для поддержки обоих типов доступа
class DocumentAccessBase(BaseModel):
    access_level: str
    user_id: Optional[int] = None
    group_id: Optional[int] = None


class DocumentAccessCreate(DocumentAccessBase):
    pass


class DocumentAccessInDB(DocumentAccessBase):
    id: int
    document_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# Обновим DocumentInDB для включения информации о групповом доступе
class DocumentInDB(DocumentBase):
    id: int
    creator_id: int
    current_version_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    shared_users: List[User] = []
    shared_groups: List[UserGroupInDB] = []

    class Config:
        orm_mode = True