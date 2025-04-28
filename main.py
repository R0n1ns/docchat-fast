import os
import uvicorn
from app import create_app
from app.db.base import Base
from app.models.document import Document, DocumentVersion
from app.models.user import User
from app.models.token import RefreshToken
from sqlalchemy import create_engine
from app.core.config import settings

# Create FastAPI app
app = create_app()

# Create tables on startup
@app.on_event("startup")
async def create_tables():
    # Create tables using sync SQLAlchemy for simplicity
    # This is only for development, in production migrations should be used
    sync_db_url = str(settings.DATABASE_URL).replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_db_url)
    Base.metadata.create_all(bind=engine)

# This is used by Gunicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
