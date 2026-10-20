# ============================================================================
# FILE:       backend/app/routers/__init__.py
# PURPOSE:    Package marker for FastAPI API route handlers under /api/v1.
# HOW IT WORKS: Re-exports APIRouter instances so main.py can mount them cleanly.
# USED BY / DEPENDS ON: app/main.py.
# KEY CONCEPTS: Modular routing, API versioning, separation of concerns.
# ============================================================================

"""FastAPI routers mounted under the API version prefix."""

# Individual domain routers.
from app.routers.users import router as users_router
from app.routers.tasks import router as tasks_router
from app.routers.comments import router as comments_router
from app.routers.transfer import router as transfer_router
from app.routers.admin import router as admin_router

__all__ = [
    "users_router",
    "tasks_router",
    "comments_router",
    "transfer_router",
    "admin_router",
]
