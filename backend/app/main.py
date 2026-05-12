import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.logging_config import setup_logging
from app.middleware import RequestIDMiddleware
from app.routers import auth, documents, expert, quiz, chat, flashcards
from app.services.llm_service import llm_service
from app.services.cache_service import cache

# Configure logging before anything else creates a logger
setup_logging(log_level=settings.log_level, log_format=settings.log_format)

logger = logging.getLogger(__name__)

app = FastAPI(title="LearnLoop API", version="0.1.0")

# RequestIDMiddleware must come before CORSMiddleware in the stack
# (outermost middleware is added last in Starlette)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(quiz.router)
app.include_router(chat.router)
app.include_router(flashcards.router)
app.include_router(expert.router)


@app.on_event("startup")
async def startup() -> None:
    if settings.jwt_secret.startswith("CHANGE-ME"):
        logger.warning(
            "JWT_SECRET is set to the default placeholder. "
            "Set a strong JWT_SECRET (>=32 chars) before deploying to production."
        )
    if settings.use_database:
        from app.database import engine, Base
        # Ensure ORM models are imported so metadata is populated
        from app import db_models  # noqa: F401
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection verified")
        except Exception as exc:
            logger.error("Database connection failed: %s", exc)
            raise RuntimeError(f"Cannot start: database unreachable — {exc}") from exc
        # Dev convenience: auto-create tables on SQLite so signup/login work
        # without running alembic. Postgres should still go through migrations.
        if settings.async_database_url.startswith("sqlite"):
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("SQLite dev DB: ensured tables exist via create_all")


@app.on_event("shutdown")
async def shutdown() -> None:
    if hasattr(cache, "close"):
        await cache.close()  # type: ignore[attr-defined]
    if settings.use_database:
        from app.database import engine
        await engine.dispose()


@app.get("/api/health")
async def health_check():
    llm_ok = await llm_service.health_check()
    model = (
        settings.groq_model if settings.llm_provider == "groq"
        else settings.ollama_model
    )
    return {
        "status": "ok" if llm_ok else "degraded",
        "llm": "connected" if llm_ok else "disconnected",
        "provider": settings.llm_provider,
        "model": model,
        "database": "enabled" if settings.use_database else "in-memory",
        "cache": settings.cache_backend,
    }


@app.delete("/api/cache")
async def clear_cache():
    """Admin endpoint: clear all cached quiz generations."""
    await cache.clear()
    return {"status": "cleared"}
