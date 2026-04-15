from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM provider: "ollama" or "groq"
    llm_provider: str = "ollama"

    # Ollama settings (used when llm_provider == "ollama")
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:latest"

    # Groq settings (used when llm_provider == "groq")
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_request_timeout: float = 60.0          # 70B needs more headroom than instant
    # Free-tier rate limit pacing: sleep this many seconds between SSE batches
    # when using Groq. 6 000 TPM / ~2 000 tokens per request ≈ 3 req/min safe.
    # 20 s between calls → ≤ 3 calls in any 60 s window → stays under limit.
    # Set to 0 to disable (e.g. paid tier).
    groq_inter_batch_sleep: float = 20.0

    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50
    default_num_questions: int = 10
    cors_origins: str = "http://localhost:3000"

    # LLM performance controls
    # With batch_size=1 a single MCQ question needs ~200-400 output tokens.
    # 600 is generous; 1500 wasted 3× the Groq TPM budget unnecessarily.
    llm_num_predict_json: int = 600
    llm_num_predict_text: int = 1024
    llm_request_timeout: float = 60.0  # per attempt; 3 retries = 180s max
    llm_max_prompt_chars: int = 8000   # conservative; keeps total tokens well within num_ctx
    llm_num_ctx: int = 8192            # context window (override in .env for model size)

    # Quiz generation
    quiz_batch_size: int = 1           # questions per LLM call (1 = safest for free-tier Groq)
    quiz_temperature: float = 0.5      # higher = more creative/diverse; 70B keeps JSON valid at 0.5
    quiz_dedup_threshold: float = 0.7  # TF-IDF cosine similarity above this = reject as duplicate

    # Database (PostgreSQL via asyncpg, or SQLite for tests)
    database_url: str = "postgresql+asyncpg://learnloop:learnloop@localhost:5432/learnloop"
    db_echo: bool = False          # set True to log all SQL statements
    use_database: bool = False     # False = in-memory (local dev), True = PostgreSQL

    # Cache backend: "memory" or "redis"
    cache_backend: str = "memory"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 1800

    @property
    def async_database_url(self) -> str:
        """Normalise any postgres:// / postgresql:// URL to postgresql+asyncpg://."""
        url = self.database_url
        if "+asyncpg" in url:
            return url  # already correct
        if url.startswith("postgres://"):
            return "postgresql+asyncpg://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + url[len("postgresql://"):]
        return url

    # Logging
    log_level: str = "INFO"
    log_format: str = "text"  # "text" for dev, "json" for production

    model_config = {"env_file": ".env"}


settings = Settings()
