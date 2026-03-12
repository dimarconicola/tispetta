from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import public_router as auth_public_router
from app.api.routes.auth import router as auth_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.opportunities import router as opportunities_router
from app.api.routes.profile import router as profile_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(auth_public_router)
api_router.include_router(profile_router)
api_router.include_router(opportunities_router)
api_router.include_router(notifications_router)
api_router.include_router(admin_router)
