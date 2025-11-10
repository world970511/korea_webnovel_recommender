"""
Vector Database Service using ChromaDB
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from backend.app.config import settings
from backend.app.services.embedding import embedding_service


class VectorDBService:
    """Service for managing ChromaDB vector database"""

    def __init__(self):
        """Initialize ChromaDB client"""
        self.persist_directory = settings.chroma_persist_directory
        self.collection_name = settings.chroma_collection_name
        self._client = None
        self._collection = None

    def _get_client(self) -> chromadb.Client:
        """Lazy load ChromaDB client"""
        if self._client is None:
            print(f"Initializing ChromaDB at: {self.persist_directory}")
            self._client = chromadb.Client(ChromaSettings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))
        return self._client

    def _get_collection(self):
        """Get or create collection"""
        if self._collection is None:
            client = self._get_client()
            try:
                self._collection = client.get_collection(name=self.collection_name)
                print(f"Loaded existing collection: {self.collection_name}")
            except Exception:
                self._collection = client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Korean web novel embeddings"}
                )
                print(f"Created new collection: {self.collection_name}")
        return self._collection

    def add_novels(self, novels: List[Dict[str, Any]]) -> None:
        """
        Add novels to the vector database

        Args:
            novels: List of novel dictionaries with keys:
                    title, author, description, platform, url, keywords
        """
        collection = self._get_collection()

        documents = []
        metadatas = []
        ids = []

        for novel in novels:
            # Create searchable text from novel information
            searchable_text = f"{novel['title']} {novel['description']} {' '.join(novel.get('keywords', []))}"
            documents.append(searchable_text)

            # Store metadata
            metadata = {
                "title": novel["title"],
                "author": novel["author"],
                "description": novel["description"],
                "platform": novel["platform"],
                "url": novel["url"],
                "keywords": ",".join(novel.get("keywords", [])),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            metadatas.append(metadata)

            # Generate unique ID
            novel_id = novel.get("id", str(uuid.uuid4()))
            ids.append(str(novel_id))

        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Added {len(novels)} novels to the database")

    def search_novels(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for novels similar to the query

        Args:
            query: Search query text
            limit: Maximum number of results to return

        Returns:
            List of novel results with similarity scores
        """
        collection = self._get_collection()

        # Generate embedding for query
        query_embedding = embedding_service.embed_query(query)

        # Search in ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )

        # Format results
        novels = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i, novel_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i] if "distances" in results else 0

                # Convert distance to similarity score (1 - normalized distance)
                similarity_score = 1 - min(distance, 1.0)

                novel = {
                    "id": int(novel_id) if novel_id.isdigit() else hash(novel_id) % 10000,
                    "title": metadata["title"],
                    "author": metadata["author"],
                    "description": metadata["description"],
                    "platform": metadata["platform"],
                    "url": metadata["url"],
                    "similarity_score": round(similarity_score, 4),
                    "keywords": metadata["keywords"].split(",") if metadata["keywords"] else []
                }
                novels.append(novel)

        return novels

    def get_novel_by_id(self, novel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific novel by ID

        Args:
            novel_id: Novel ID

        Returns:
            Novel data or None if not found
        """
        collection = self._get_collection()

        try:
            result = collection.get(ids=[str(novel_id)])
            if result["ids"]:
                metadata = result["metadatas"][0]
                return {
                    "id": int(novel_id) if novel_id.isdigit() else hash(novel_id) % 10000,
                    "title": metadata["title"],
                    "author": metadata["author"],
                    "description": metadata["description"],
                    "platform": metadata["platform"],
                    "url": metadata["url"],
                    "keywords": metadata["keywords"].split(",") if metadata["keywords"] else [],
                    "created_at": metadata.get("created_at", datetime.utcnow().isoformat()),
                    "updated_at": metadata.get("updated_at", datetime.utcnow().isoformat())
                }
        except Exception as e:
            print(f"Error getting novel {novel_id}: {e}")

        return None

    def get_all_novels(self) -> List[Dict[str, Any]]:
        """Get all novels from the database"""
        collection = self._get_collection()

        try:
            result = collection.get()
            novels = []
            for i, novel_id in enumerate(result["ids"]):
                metadata = result["metadatas"][i]
                novels.append({
                    "id": int(novel_id) if novel_id.isdigit() else hash(novel_id) % 10000,
                    "title": metadata["title"],
                    "author": metadata["author"],
                    "platform": metadata["platform"],
                    "keywords": metadata["keywords"].split(",") if metadata["keywords"] else []
                })
            return novels
        except Exception as e:
            print(f"Error getting all novels: {e}")
            return []

    def count_novels(self) -> int:
        """Get total number of novels in database"""
        collection = self._get_collection()
        return collection.count()


# Singleton instance
vector_db_service = VectorDBService()
