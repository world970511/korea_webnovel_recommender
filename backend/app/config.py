"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Backend Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # Embedding Model Configuration
    embedding_model: str = "jhgan/ko-sroberta-multitask"
    use_ollama: bool = False
    ollama_model: Optional[str] = None

    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "webnovel_db"

    # API Configuration
    max_query_length: int = 140
    default_search_limit: int = 10
    max_search_limit: int = 50

    # Skyvern + Ollama Configuration
    enable_skyvern: bool = False
    enable_ollama: bool = True
    ollama_server_url: str = "http://localhost:11434"
    skyvern_ollama_model: str = "qwen2.5:7b-instruct"

    # Crawler Configuration
    crawler_enabled: bool = False
    crawler_batch_size: int = 20
    crawler_delay_seconds: int = 2

    # Platform Credentials (for adult content)
    naver_username: Optional[str] = None
    naver_password: Optional[str] = None
    kakao_username: Optional[str] = None
    kakao_password: Optional[str] = None
    ridi_username: Optional[str] = None
    ridi_password: Optional[str] = None

    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from old .env files


settings = Settings()
