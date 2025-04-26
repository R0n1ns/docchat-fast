from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

class Base(AsyncAttrs, DeclarativeBase):
    pass

# Import all models here for Alembic autogenerate to work
from app.models.user import User
from app.models.document import Document, DocumentVersion
from app.models.token import RefreshToken
