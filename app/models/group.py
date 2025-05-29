from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserGroup(Base):
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    members = relationship("User", secondary="user_group_members", back_populates="groups")
    leader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    leader = relationship("User", foreign_keys=[leader_id])

class UserGroupMember(Base):
    __tablename__ = "user_group_members"

    group_id = Column(Integer, ForeignKey("user_groups.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())