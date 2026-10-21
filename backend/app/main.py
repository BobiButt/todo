# ============================================================================
# FILE:       backend/app/main.py
# PURPOSE:    FastAPI application entry point. Configures CORS, mounts API routers
#             under /api/v1, defines the /health heartbeat endpoint, and configures
#             interactive OpenAPI documentation.
# HOW IT WORKS: Instantiates FastAPI app with application metadata. Attaches
#             CORSMiddleware using allowed origins from settings. Mounts routers
#             from app/routers. Provides GET /health for deployment readiness checks.
# USED BY / DEPENDS ON: uvicorn app.main:app, tests/conftest.py, frontend HTTP client.
# KEY CONCEPTS: Application factory, CORS middleware, API prefix mounting,
#             health check endpoint, OpenAPI schema generation.
# ============================================================================

"""Main FastAPI application entry point and configuration."""

# contextlib asynccontextmanager for application lifespan management.
from contextlib import asynccontextmanager

# typing AsyncIterator for lifespan typing.
from typing import AsyncIterator

# FastAPI application class and routing components.
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Application configuration settings.
from app.config import settings

# Router instances.
from app.routers.admin import router as admin_router
from app.routers.assistant import router as assistant_router
from app.routers.auth import router as auth_router
from app.routers.comments import router as comments_router
from app.routers.tasks import router as tasks_router
from app.routers.transfer import router as transfer_router
from app.routers.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager for startup and shutdown events.

    Parameters:
        app (FastAPI): The running FastAPI application instance.

    Yields:
        None: Hands execution control to the application server.
    """
    # Startup: Application is ready to receive requests.
    yield
    # Shutdown: Clean up any long-running resources if needed.


# Create FastAPI application instance with descriptive title and OpenAPI docs paths.
app = FastAPI(
    title="TaskFlow API",
    description=(
        "Production-quality Todo Application backend with role-based access control, "
        "task comments, CSV/JSON import & export, and administration metrics."
    ),
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS) so Vite dev server can call endpoints.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get(
    "/health",
    tags=["System"],
    summary="Health check endpoint",
    description="Returns service health status and current operating environment.",
    status_code=status.HTTP_200_OK,
)
async def health_check() -> JSONResponse:
    """Service heartbeat and readiness check.

    Returns:
        JSONResponse: Status dictionary confirming backend is alive.
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "environment": settings.environment,
            "version": "1.0.0",
        }
    )


@app.get(
    "/",
    tags=["System"],
    summary="Home / server status",
    description="Returns a welcome message and useful links to verify the backend is running.",
    status_code=status.HTTP_200_OK,
)
async def home() -> JSONResponse:
    """Backend home endpoint.

    Returns:
        JSONResponse: Welcome message with links to health check and API docs.
    """
    docs_hint = (
        f"{settings.app_prefix}/docs (enabled in development)"
        if settings.is_development
        else "disabled in production"
    )
    return JSONResponse(
        content={
            "message": "TaskFlow API is running",
            "status": "healthy",
            "version": "1.0.0",
            "environment": settings.environment,
            "health": "/health",
            "api_prefix": settings.app_prefix,
            "docs": docs_hint,
        }
    )


# Mount versioned API routers under the configured prefix (/api/v1).
app.include_router(auth_router, prefix=settings.app_prefix)
app.include_router(users_router, prefix=settings.app_prefix)
app.include_router(transfer_router, prefix=settings.app_prefix)
app.include_router(tasks_router, prefix=settings.app_prefix)
app.include_router(comments_router, prefix=settings.app_prefix)
app.include_router(admin_router, prefix=settings.app_prefix)
app.include_router(assistant_router, prefix=settings.app_prefix)
