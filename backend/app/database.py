"""Async SQLAlchemy engine, session factory, and FastAPI dependency."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


# Engine is created lazily — only connects when USE_DATABASE=true
# SQLite (dev) doesn't support pool_size/max_overflow; Postgres (prod) does.
_url = settings.async_database_url
if _url.startswith("sqlite"):
    engine = create_async_engine(_url, echo=settings.db_echo)
else:
    engine = create_async_engine(
        _url,
        echo=settings.db_echo,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    """FastAPI dependency: yields a DB session (or None when USE_DATABASE=false).

    Callers pass the session straight to service methods which handle None
    by falling back to the in-memory dict path.
    """
    if not settings.use_database:
        yield None
        return
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
