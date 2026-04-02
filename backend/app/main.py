from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import documents, quiz, chat
from app.services.llm_service import llm_service
from app.services.cache_service import cache

app = FastAPI(title="LearnLoop API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(quiz.router)
app.include_router(chat.router)


@app.get("/api/health")
async def health_check():
    llm_ok = await llm_service.health_check()
    return {
        "status": "ok" if llm_ok else "degraded",
        "llm": "connected" if llm_ok else "disconnected",
        "model": settings.ollama_model,
    }


@app.delete("/api/cache")
async def clear_cache():
    """Admin endpoint: clear all cached quiz generations."""
    await cache.clear()
    return {"status": "cleared"}
