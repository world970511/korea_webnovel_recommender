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

    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
