from fastapi import APIRouter, Depends
from typing import List

from starlette import status

from app.core.config import settings
from app.schemas.env import EnvVarsResponse
from app.schemas.user import User

router = APIRouter()

@router.get("/env", response_model=List[EnvVarsResponse], dependencies=[])
async def get_environment_vars():
    """Get exposed environment variables"""
    return [
        {"name": var, "value": str(getattr(settings, var, ""))}
        for var in settings.EXPOSED_ENV_VARS
    ]

@router.get("/health", dependencies=[])
async def get_environment_vars():
    """Get exposed environment variables"""
    return status.HTTP_200_OK
