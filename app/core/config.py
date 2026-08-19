from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_env: str = "development"
    log_level: str = "INFO"

    # Data directories
    data_dir: Path = Path("data")
    raw_data_dir: Path = Path("data/raw")
    processed_data_dir: Path = Path("data/processed")
    normalized_data_dir: Path = Path("data/normalized")
    evaluation_data_dir: Path = Path("data/evaluation")
    
    #Database
    database_url : str
    
    # Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(
        default=60,
        ge=1,
    )

    # Google Sign-In (server-side ID token verification). Empty by
    # default - Google auth endpoints reject requests until this is
    # configured with a real Google OAuth Web Client ID.
    google_client_id: str = ""
    
    # Models
    embedding_model: str = "BAAI/bge-m3"
    llm_model: str = ""

    # LLM explanation generation (OpenRouter, OpenAI-compatible API).
    # The LLM is an explanation layer only - it never computes
    # scores/eligibility/decisions. Disabled by default so that
    # existing/automated tests never make live network calls; the
    # deployed .env used for the live demo turns this on explicitly.
    enable_llm_explanations: bool = False
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-oss-20b:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_timeout_seconds: float = Field(default=15.0, gt=0.0)

    # Retrieval / ranking
    top_k: int = Field(default=10, ge=1)
    min_match_score: float = Field(default=0.0, ge=0.0, le=1.0)

    bm25_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    dense_weight: float = Field(default=0.5, ge=0.0, le=1.0)

    # Feature flags
    enable_semantic_search: bool = True
    enable_llm_reranking: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()