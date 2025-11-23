from app.api.api import router as api_router
from app.api.auth import router as auth_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(api_router)
router.include_router(auth_router)

__all__ = ["router"]
