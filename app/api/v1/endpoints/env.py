from fastapi import APIRouter, Depends
from typing import List

from app.core.config import settings
from app.schemas.env import EnvVarsResponse
from app.api.dependencies import get_current_active_admin
from app.schemas.user import User

router = APIRouter()

@router.get("/env", response_model=List[EnvVarsResponse])
async def get_environment_vars(
):
    """Get exposed environment variables (Admin only)"""
    return [
        {"name": var, "value": str(getattr(settings, var, ""))}
        for var in settings.EXPOSED_ENV_VARS
    ]

