from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:latest"
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50
    default_num_questions: int = 10
    cors_origins: str = "http://localhost:3000"

    # LLM performance controls
    llm_num_predict_json: int = 1024   # was 512 — not enough for 3-question batches
    llm_num_predict_text: int = 1024
    llm_request_timeout: float = 60.0  # per attempt; 3 retries = 180s max
    llm_max_prompt_chars: int = 8000   # conservative; keeps total tokens well within num_ctx
    llm_num_ctx: int = 8192            # context window (override in .env for model size)

    # Quiz generation
    quiz_batch_size: int = 2           # questions per LLM call (reduce for smaller models)

    # Caching
    cache_ttl_seconds: int = 1800

    model_config = {"env_file": ".env"}


settings = Settings()
