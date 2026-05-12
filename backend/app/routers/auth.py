"""Authentication routes: signup, login, me."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.db_models import User
from app.deps import get_current_user
from app.models import (
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    create_access_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _require_db(db: AsyncSession | None) -> AsyncSession:
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Auth requires database — set USE_DATABASE=true",
        )
    return db


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(
    req: SignupRequest,
    db: AsyncSession | None = Depends(get_db),
) -> TokenResponse:
    db = _require_db(db)
    email = req.email.lower()

    existing = await db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password(req.password),
        role="user",
    )
    db.add(user)
    await db.flush()

    token = create_access_token(str(user.id), user.role)
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=str(user.id), email=user.email, role=user.role),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession | None = Depends(get_db),
) -> TokenResponse:
    db = _require_db(db)
    email = req.email.lower()

    user = await db.scalar(select(User).where(User.email == email))
    # Same error message both branches to avoid email enumeration leak.
    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong email or password")

    token = create_access_token(str(user.id), user.role)
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=str(user.id), email=user.email, role=user.role),
    )


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=user["id"], email=user["email"], role=user["role"])
