from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db, get_current_active_admin
from app.crud import crud_group
from app.schemas.group import UserGroupCreate, UserGroupUpdate, UserGroupInDB
from app.schemas.user import User

router = APIRouter()

@router.post("", response_model=UserGroupInDB)
async def create_group(
    group_in: UserGroupCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    return await crud_group.group_crud.create(db, group_in)

@router.post("/{group_id}/members/{user_id}")
async def add_member_to_group(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    return await crud_group.group_crud.add_member(db, group_id, user_id)

@router.delete("/{group_id}/members/{user_id}")
async def remove_member_from_group(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    success = await crud_group.group_crud.remove_member(db, group_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"status": "success"}