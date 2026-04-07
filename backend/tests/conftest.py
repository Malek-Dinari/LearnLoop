"""Shared test fixtures.

Provides an async SQLite in-memory database session for tests that
exercise database-backed code paths. No PostgreSQL server required.
"""

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base
import app.db_models  # noqa: F401 — registers all ORM tables with Base.metadata


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
