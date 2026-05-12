"""FastAPI dependency injection helpers for authentication and RBAC."""

import uuid

import jwt
from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.db_models import User
from app.services.auth_service import decode_token


def _extract_token(
    authorization: str | None,
    access_token: str | None,
) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    if access_token:
        return access_token
    return None


async def get_current_user_optional(
    authorization: str | None = Header(None),
    access_token: str | None = Query(default=None),
    db: AsyncSession | None = Depends(get_db),
) -> dict | None:
    """Returns {id, email, role} or None. Never raises - anonymous OK.

    Accepts the token via either Authorization: Bearer <t> header OR
    ?access_token=<t> query param (the latter is needed for SSE EventSource
    which cannot set headers).
    """
    token = _extract_token(authorization, access_token)
    if not token:
        return None
    try:
        payload = decode_token(token)
    except jwt.InvalidTokenError:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    if db is None:
        return {
            "id": user_id,
            "role": payload.get("role", "user"),
            "email": "",
        }

    try:
        user = await db.scalar(select(User).where(User.id == uuid.UUID(user_id)))
    except (ValueError, Exception):
        return None
    if not user:
        return None
    return {"id": str(user.id), "email": user.email, "role": user.role}


async def get_current_user(
    user: dict | None = Depends(get_current_user_optional),
) -> dict:
    """Required-auth: 401 if no/invalid token."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_role(*allowed_roles: str):
    """Returns a dependency that 403s if user.role not in allowed_roles."""

    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Requires role: {' or '.join(allowed_roles)}",
            )
        return user

    return checker
