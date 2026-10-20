# ============================================================================
# FILE:       backend/app/dependencies.py
# PURPOSE:    Single source of truth for request authentication and role
#             enforcement dependencies across the entire FastAPI application.
# HOW IT WORKS: Reads `X-User-Id` and `X-Role` headers from incoming HTTP requests.
#             Loads the User row from the database to ensure identity authenticity.
#             `require_admin` verifies the user possesses administrator rights.
#             Isolating this logic in one file allows replacing header auth with
#             JWT/OAuth in the future without touching any routers or models.
# USED BY / DEPENDS ON: imported by all routers under app/routers/*.
# KEY CONCEPTS: Dependency Injection, Role-Based Access Control (RBAC),
#             FastAPI Depends, HTTP status codes (401, 403).
# ============================================================================

"""FastAPI dependencies for role-based access control and current user resolution."""

# Header extracts custom HTTP header values from the request context.
from fastapi import Depends, Header, HTTPException, status

# AsyncSession is the SQLAlchemy session type for executing queries.
from sqlalchemy.ext.asyncio import AsyncSession

# select builds type-safe SQL query expressions.
from sqlalchemy import select

# get_db is our database session-per-request dependency.
from app.database import get_db

# User is the ORM model representing registered accounts.
from app.models.user import User

# Role is the StrEnum defining 'admin' and 'user'.
from app.schemas.common import Role


async def get_current_user(
    # x_user_id reads the custom header 'X-User-Id'. None if omitted by client.
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    # x_role reads the custom header 'X-Role'. None if omitted by client.
    x_role: str | None = Header(default=None, alias="X-Role"),
    # db is the active asynchronous database session for this request.
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the authenticated user from request headers and database.

    Parameters:
        x_user_id (str | None): Value of the X-User-Id header.
        x_role (str | None): Value of the X-Role header.
        db (AsyncSession): Database session provided by Depends(get_db).

    Returns:
        User: The active ORM User model instance.

    Raises:
        HTTPException(401): If X-User-Id header is missing or non-numeric.
        HTTPException(401): If no user exists with the given ID in the database.

    SECURITY:
        Verifies that the user exists in PostgreSQL rather than trusting headers
        blindly. Future JWT upgrade replaces header parsing with token decoding.
    """
    # Check whether the client supplied the required identification header.
    if not x_user_id:
        # Reject unauthenticated requests with HTTP 401 Unauthorized.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required 'X-User-Id' header.",
        )

    # Attempt to convert the header string into an integer primary key.
    try:
        # Parse the string into an integer.
        user_id = int(x_user_id)
    except ValueError:
        # Reject non-numeric user IDs with HTTP 401.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 'X-User-Id' header format; must be an integer.",
        )

    # Query PostgreSQL to fetch the User row matching the ID.
    query = select(User).where(User.id == user_id)
    # Execute the query asynchronously.
    result = await db.execute(query)
    # Retrieve the first matching User or None.
    user = result.scalars().first()

    # If the user row does not exist in the database, reject the request.
    if not user:
        # Reject requests claiming non-existent users.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User with ID {user_id} not found.",
        )

    # Return the verified User entity.
    return user


async def require_admin(
    # current_user resolves the active User row first using get_current_user.
    current_user: User = Depends(get_current_user),
) -> User:
    """FastAPI dependency ensuring the requesting user has the ADMIN role.

    Parameters:
        current_user (User): The verified user from get_current_user.

    Returns:
        User: The same user entity if they have the ADMIN role.

    Raises:
        HTTPException(403): If the user's role is not 'admin'.
    """
    # Compare the user's stored role against the required Role.ADMIN enum value.
    if current_user.role != Role.ADMIN:
        # Reject non-administrators with HTTP 403 Forbidden.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: administrator privileges required.",
        )

    # Return the authorized admin user.
    return current_user
