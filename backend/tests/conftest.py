"""Shared test fixtures.

Provides an async SQLite in-memory database session for tests that
exercise database-backed code paths. No PostgreSQL server required.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
from app.config import settings as _settings
import app.db_models  # noqa: F401 — registers all ORM tables with Base.metadata

# Tests default to in-memory mode regardless of what .env sets for dev.
# Fixtures that need a DB (e.g. auth_app) flip this on themselves.
_settings.use_database = False


@pytest.fixture
async def db() -> AsyncSession:
    """Async SQLite in-memory session — created fresh per test, disposed after."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def auth_app():
    """FastAPI app with get_db overridden to use a fresh in-memory sqlite DB.

    Yields (app, session_factory). Session factory creates fresh sessions
    that share the same connection-pool engine, so all tests see the same
    rows the routes wrote.
    """
    from app.main import app
    from app.config import settings

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    # Force routes to treat us as DB-backed even though we're sqlite.
    original_use_db = settings.use_database
    settings.use_database = True
    try:
        yield app, session_factory
    finally:
        settings.use_database = original_use_db
        app.dependency_overrides.pop(get_db, None)
        await engine.dispose()


@pytest.fixture
async def auth_client(auth_app):
    app, _ = auth_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def make_user(auth_app):
    """Factory: create a user row and return {token, user_id, email, role, headers}."""
    from app.db_models import User
    from app.services.auth_service import create_access_token, hash_password

    _, session_factory = auth_app

    async def _make(email: str | None = None, role: str = "user", password: str = "password123") -> dict:
        email = email or f"u-{uuid.uuid4().hex[:8]}@test.com"
        async with session_factory() as session:
            user = User(
                id=uuid.uuid4(),
                email=email,
                password_hash=hash_password(password),
                role=role,
            )
            session.add(user)
            await session.commit()
            uid = str(user.id)
        token = create_access_token(uid, role)
        return {
            "id": uid,
            "email": email,
            "role": role,
            "password": password,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }

    return _make
