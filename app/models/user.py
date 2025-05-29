from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    position = Column(String)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")  # user, manager, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    documents = relationship("Document", back_populates="creator")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    groups = relationship("UserGroup", secondary="user_group_members", back_populates="members")