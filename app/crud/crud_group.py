from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.group import UserGroup, UserGroupMember
from app.schemas.group import UserGroupCreate, UserGroupUpdate

class CRUDGroup:
    async def create(self, db: AsyncSession, obj_in: UserGroupCreate) -> UserGroup:
        db_obj = UserGroup(**obj_in.dict())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, group_id: int, obj_in: UserGroupUpdate) -> UserGroup:
        group = await db.get(UserGroup, group_id)
        if not group:
            return None
        for key, value in obj_in.dict(exclude_unset=True).items():
            setattr(group, key, value)
        await db.commit()
        await db.refresh(group)
        return group

    async def add_member(self, db: AsyncSession, group_id: int, user_id: int) -> UserGroupMember:
        member = UserGroupMember(group_id=group_id, user_id=user_id)
        db.add(member)
        await db.commit()
        return member

    async def remove_member(self, db: AsyncSession, group_id: int, user_id: int) -> bool:
        result = await db.execute(
            select(UserGroupMember)
            .filter(UserGroupMember.group_id == group_id)
            .filter(UserGroupMember.user_id == user_id)
        )
        member = result.scalars().first()
        if member:
            await db.delete(member)
            await db.commit()
            return True
        return False

group_crud = CRUDGroup()