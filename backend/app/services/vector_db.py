"""
Vector Database Service using PostgreSQL + PGVector
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from backend.app.config import settings
from backend.app.services.embedding import embedding_service

logger = logging.getLogger(__name__)


class VectorDBService:
    """Service for managing PostgreSQL with PGVector extension"""

    def __init__(self):
        """Initialize PostgreSQL connection"""
        self._connection = None
        self._setup_complete = False

    def _get_connection(self):
        """Get or create database connection"""
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg2.connect(
                    host=settings.postgres_host,
                    port=settings.postgres_port,
                    user=settings.postgres_user,
                    password=settings.postgres_password,
                    database=settings.postgres_db,
                    cursor_factory=RealDictCursor
                )
                # Register pgvector type
                register_vector(self._connection)
                logger.info("Connected to PostgreSQL database")
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                raise

        return self._connection

    def _ensure_setup(self):
        """Ensure database schema is set up"""
        if self._setup_complete:
            return

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Create pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                # Create novels table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS novels (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        author TEXT NOT NULL,
                        description TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        url TEXT NOT NULL,
                        keywords TEXT[] NOT NULL DEFAULT '{}',
                        embedding vector(768),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Create index for vector similarity search
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS novels_embedding_idx
                    ON novels USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """)

                # Create index for platform filtering
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS novels_platform_idx
                    ON novels (platform);
                """)

                conn.commit()
                self._setup_complete = True
                logger.info("Database schema setup complete")

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to setup database schema: {e}")
            raise

    def add_novels(self, novels: List[Dict[str, Any]]) -> None:
        """
        Add novels to the database with embeddings

        Args:
            novels: List of novel dictionaries with keys:
                    title, author, description, platform, url, keywords
        """
        self._ensure_setup()
        conn = self._get_connection()

        try:
            # Generate embeddings for all novels
            texts = [
                f"{novel['title']} {novel['description']} {' '.join(novel.get('keywords', []))}"
                for novel in novels
            ]
            embeddings = embedding_service.embed_documents(texts)

            with conn.cursor() as cur:
                for novel, embedding in zip(novels, embeddings):
                    # Check if novel already exists (by title and author)
                    cur.execute(
                        "SELECT id FROM novels WHERE title = %s AND author = %s",
                        (novel['title'], novel['author'])
                    )
                    existing = cur.fetchone()

                    if existing:
                        # Update existing novel
                        cur.execute("""
                            UPDATE novels
                            SET description = %s,
                                platform = %s,
                                url = %s,
                                keywords = %s,
                                embedding = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (
                            novel['description'],
                            novel['platform'],
                            novel['url'],
                            novel.get('keywords', []),
                            embedding,
                            existing['id']
                        ))
                    else:
                        # Insert new novel
                        cur.execute("""
                            INSERT INTO novels
                            (title, author, description, platform, url, keywords, embedding)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            novel['title'],
                            novel['author'],
                            novel['description'],
                            novel['platform'],
                            novel['url'],
                            novel.get('keywords', []),
                            embedding
                        ))

            conn.commit()
            logger.info(f"Added/Updated {len(novels)} novels to the database")

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to add novels: {e}")
            raise

    def search_novels(self, query: str, limit: int = 10, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for novels similar to the query using vector similarity

        Args:
            query: Search query text
            limit: Maximum number of results to return
            platform: Optional platform filter

        Returns:
            List of novel results with similarity scores
        """
        self._ensure_setup()
        conn = self._get_connection()

        try:
            # Generate embedding for query
            query_embedding = embedding_service.embed_query(query)

            with conn.cursor() as cur:
                if platform:
                    # Search with platform filter
                    cur.execute("""
                        SELECT
                            id,
                            title,
                            author,
                            description,
                            platform,
                            url,
                            keywords,
                            created_at,
                            updated_at,
                            1 - (embedding <=> %s::vector) as similarity_score
                        FROM novels
                        WHERE platform = %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                    """, (query_embedding, platform, query_embedding, limit))
                else:
                    # Search without filter
                    cur.execute("""
                        SELECT
                            id,
                            title,
                            author,
                            description,
                            platform,
                            url,
                            keywords,
                            created_at,
                            updated_at,
                            1 - (embedding <=> %s::vector) as similarity_score
                        FROM novels
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                    """, (query_embedding, query_embedding, limit))

                results = cur.fetchall()

            # Format results
            novels = []
            for row in results:
                novel = {
                    "id": row['id'],
                    "title": row['title'],
                    "author": row['author'],
                    "description": row['description'],
                    "platform": row['platform'],
                    "url": row['url'],
                    "keywords": list(row['keywords']) if row['keywords'] else [],
                    "similarity_score": round(float(row['similarity_score']), 4)
                }
                novels.append(novel)

            return novels

        except Exception as e:
            logger.error(f"Failed to search novels: {e}")
            raise

    def get_novel_by_id(self, novel_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific novel by ID

        Args:
            novel_id: Novel ID

        Returns:
            Novel data or None if not found
        """
        self._ensure_setup()
        conn = self._get_connection()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id,
                        title,
                        author,
                        description,
                        platform,
                        url,
                        keywords,
                        created_at,
                        updated_at
                    FROM novels
                    WHERE id = %s
                """, (novel_id,))

                row = cur.fetchone()

            if row:
                return {
                    "id": row['id'],
                    "title": row['title'],
                    "author": row['author'],
                    "description": row['description'],
                    "platform": row['platform'],
                    "url": row['url'],
                    "keywords": list(row['keywords']) if row['keywords'] else [],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get novel {novel_id}: {e}")
            return None

    def get_all_novels(self, platform: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all novels from the database with optional filtering

        Args:
            platform: Optional platform filter
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of novels
        """
        self._ensure_setup()
        conn = self._get_connection()

        try:
            with conn.cursor() as cur:
                if platform:
                    cur.execute("""
                        SELECT id, title, author, platform, keywords
                        FROM novels
                        WHERE platform = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (platform, limit, offset))
                else:
                    cur.execute("""
                        SELECT id, title, author, platform, keywords
                        FROM novels
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))

                results = cur.fetchall()

            novels = []
            for row in results:
                novels.append({
                    "id": row['id'],
                    "title": row['title'],
                    "author": row['author'],
                    "platform": row['platform'],
                    "keywords": list(row['keywords']) if row['keywords'] else []
                })

            return novels

        except Exception as e:
            logger.error(f"Failed to get all novels: {e}")
            return []

    def count_novels(self, platform: Optional[str] = None) -> int:
        """
        Get total number of novels in database

        Args:
            platform: Optional platform filter

        Returns:
            Count of novels
        """
        self._ensure_setup()
        conn = self._get_connection()

        try:
            with conn.cursor() as cur:
                if platform:
                    cur.execute("SELECT COUNT(*) as count FROM novels WHERE platform = %s", (platform,))
                else:
                    cur.execute("SELECT COUNT(*) as count FROM novels")

                result = cur.fetchone()
                return result['count'] if result else 0

        except Exception as e:
            logger.error(f"Failed to count novels: {e}")
            return 0

    def get_all_keywords(self) -> List[str]:
        """
        Get all unique keywords from the database

        Returns:
            List of unique keywords
        """
        self._ensure_setup()
        conn = self._get_connection()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT unnest(keywords) as keyword
                    FROM novels
                    ORDER BY keyword
                """)

                results = cur.fetchall()
                return [row['keyword'] for row in results]

        except Exception as e:
            logger.error(f"Failed to get keywords: {e}")
            return []

    def close(self):
        """Close database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Closed PostgreSQL connection")

    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# Singleton instance
vector_db_service = VectorDBService()
