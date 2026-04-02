from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:latest"
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50
    default_num_questions: int = 10
    cors_origins: str = "http://localhost:3000"

    # LLM performance controls
    llm_num_predict_json: int = 512
    llm_num_predict_text: int = 1024
    llm_request_timeout: float = 90.0
    llm_max_prompt_chars: int = 10000

    # Quiz generation
    quiz_batch_size: int = 3

    # Caching
    cache_ttl_seconds: int = 1800

    model_config = {"env_file": ".env"}


settings = Settings()
