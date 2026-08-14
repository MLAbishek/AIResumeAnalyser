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

    # Models
    embedding_model: str = ""
    llm_model: str = ""

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