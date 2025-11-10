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

    # ChromaDB Configuration
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "webnovels"

    # API Configuration
    max_query_length: int = 140
    default_search_limit: int = 10
    max_search_limit: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
