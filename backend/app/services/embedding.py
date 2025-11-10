"""
Embedding Service using LangChain
"""
from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from backend.app.config import settings


class EmbeddingService:
    """Service for generating embeddings using LangChain"""

    def __init__(self):
        """Initialize embedding model"""
        self.model_name = settings.embedding_model
        self._embeddings = None

    def _get_embeddings(self) -> HuggingFaceEmbeddings:
        """Lazy load embeddings model"""
        if self._embeddings is None:
            print(f"Loading embedding model: {self.model_name}")
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            print("Embedding model loaded successfully")
        return self._embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query text

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding
        """
        embeddings = self._get_embeddings()
        return embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        embeddings = self._get_embeddings()
        return embeddings.embed_documents(texts)


# Singleton instance
embedding_service = EmbeddingService()
