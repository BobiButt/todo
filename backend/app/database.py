# ============================================================================
# FILE:       backend/app/database.py
# PURPOSE:    Own everything that touches the database connection: the async
#             engine, the session factory, the shared declarative Base that
#             all models inherit from, and the `get_db` dependency that gives
#             each request its own session.
# HOW IT WORKS: On import we build one async engine (a pool of reusable
#             connections) from settings.database_url. Routes ask for a session
#             via FastAPI's Depends(get_db); the session is closed by this
#             generator even if the route raises an error.
# USED BY / DEPENDS ON: imported by every model (Base), every router (get_db),
#             alembic/env.py (Base.metadata), tests (fresh engine per run).
# KEY CONCEPTS: async engine, connection pooling, session-per-request,
#             declarative base, dependency injection, health-check ping.
# ============================================================================

"""Async SQLAlchemy engine, session factory, declarative Base, get_db."""

# create_async_engine builds a pool of async DB connections (uses asyncpg).
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# DeclarativeBase is SQLAlchemy 2.0's base class: maps Python classes -> tables.
from sqlalchemy.orm import DeclarativeBase

# text() is required to run literal SQL such as "SELECT 1" for health checks.
from sqlalchemy import text

# AsyncGenerator types the get_db generator precisely for type checkers.
from collections.abc import AsyncGenerator

# Our typed settings object — database_url and environment live there.
from app.config import settings


class Base(DeclarativeBase):
    """Shared declarative base for every ORM model.

    Why a single Base? All models inherit from it, so `Base.metadata`
    automatically knows every table — Alembic uses that knowledge to generate
    migrations, and tests can create the whole schema with one call.

    Example:
        class Task(Base):
            __tablename__ = "tasks"
    """

    # Nothing extra to configure: SQLAlchemy 2.0 infers column types from
    # `Mapped[...]` annotations. The class exists to be inherited.


def _build_engine() -> AsyncEngine:
    """Create the application's async SQLAlchemy engine.

    Parameters: none (reads settings.database_url).

    Returns:
        AsyncEngine: pooled connection object used for the app's whole life.

    Side effects:
        Establishes no connections yet — connections open lazily on first
        query and return to the pool afterwards.

    NOTE: pool_pre_ping=True issues "SELECT 1" before handing out a pooled
    connection, transparently discarding connections PostgreSQL dropped
    overnight (prevents "server closed the connection unexpectedly").
    """
    return create_async_engine(
        settings.database_url,
        echo=False,  # True would log every SQL statement (useful when debugging)
        pool_pre_ping=True,
    )


# The one engine for the running application (created once at import time).
engine: AsyncEngine = _build_engine()

# async_sessionmaker builds new AsyncSession objects on demand.
# expire_on_commit=False: after commit() objects keep their values, so routers
# can read attributes without triggering a lazy refresh query (which would
# fail outside the request scope anyway).
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # explicit flush() calls only — avoids surprise INSERTs
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding one database session per request.

    Yields:
        AsyncSession: an open session bound to this request.

    Side effects / errors:
        - On normal exit the session is closed (connection returned to pool).
        - On an exception inside the route the transaction is rolled back
          first, so a half-written request never leaves the DB inconsistent.

    Usage (in a router):
        @router.post("/tasks")
        async def create_task(db: AsyncSession = Depends(get_db)):
            ...

    NOTE: the route — not this function — decides when to commit. Commits are
    explicit so the all-or-nothing behaviour of imports is obvious.
    """
    # factory() opens a fresh session for this request only.
    async with AsyncSessionLocal() as session:
        try:
            # Hand control to the route handler.
            yield session
        except Exception:
            # Any unhandled error: undo uncommitted work, then re-raise so the
            # client still receives the proper error status code.
            await session.rollback()
            raise
        finally:
            # Always release the connection back to the pool.
            await session.close()


async def ping_database() -> bool:
    """Check that PostgreSQL answers a trivial query (for GET /health).

    Returns:
        bool: True when a round-trip query succeeded, False otherwise.

    Errors:
        Swallows every exception on purpose — a health endpoint must report
        "database down" instead of crashing with a 500.
    """
    try:
        # async with engine.connect() checks out a pooled connection...
        async with engine.connect() as connection:
            # ...and runs the cheapest possible query.
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 — health checks must never propagate
        return False


async def dispose_engine() -> None:
    """Close all pooled connections (used by tests and graceful shutdown).

    Returns: None.

    Side effects: after this call the engine opens fresh connections on demand.
    """
    await engine.dispose()
