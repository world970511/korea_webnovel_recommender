"""
Base Crawler Class

Provides common functionality for all platform-specific crawlers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """
    Abstract base class for platform-specific crawlers.

    Each platform crawler should inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, skyvern_client, platform_name: str):
        """
        Initialize the crawler.

        Args:
            skyvern_client: Configured Skyvern client instance
            platform_name: Name of the platform (e.g., "naver", "kakao", "ridi")
        """
        self.client = skyvern_client
        self.platform_name = platform_name
        self.logger = logging.getLogger(f"{__name__}.{platform_name}")

    @abstractmethod
    async def crawl_genre(
        self,
        genre: str,
        limit: int = 20,
        include_adult: bool = False
    ) -> List[Dict]:
        """
        Crawl novels from a specific genre.

        Args:
            genre: Genre name (e.g., "판타지", "로맨스", "무협")
            limit: Maximum number of novels to collect
            include_adult: Whether to include adult content (requires login)

        Returns:
            List of novel dictionaries with keys:
                - title: str
                - author: str
                - description: str
                - platform: str
                - url: str
                - keywords: List[str]
        """
        pass

    @abstractmethod
    async def login(self, username: str, password: str) -> bool:
        """
        Login to the platform (required for adult content).

        Args:
            username: Platform username
            password: Platform password

        Returns:
            True if login successful, False otherwise
        """
        pass

    def normalize_novel_data(self, raw_data: Dict) -> Dict:
        """
        Normalize raw crawled data to standard format.

        Args:
            raw_data: Raw data from Skyvern

        Returns:
            Normalized novel dictionary
        """
        return {
            "title": raw_data.get("title", "").strip(),
            "author": raw_data.get("author", "").strip(),
            "description": raw_data.get("description", "").strip(),
            "platform": self.platform_name,
            "url": raw_data.get("url", "").strip(),
            "keywords": self._extract_keywords(raw_data),
        }

    def _extract_keywords(self, raw_data: Dict) -> List[str]:
        """
        Extract and clean keywords from raw data.

        Args:
            raw_data: Raw data from Skyvern

        Returns:
            List of cleaned keywords
        """
        keywords = raw_data.get("keywords", [])

        # Handle both list and comma-separated string
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",")]

        # Clean and deduplicate
        keywords = [k for k in keywords if k]
        return list(set(keywords))

    async def crawl_multiple_genres(
        self,
        genres: List[str],
        limit_per_genre: int = 20,
        include_adult: bool = False
    ) -> List[Dict]:
        """
        Crawl novels from multiple genres.

        Args:
            genres: List of genre names
            limit_per_genre: Maximum novels per genre
            include_adult: Whether to include adult content

        Returns:
            Combined list of novels from all genres
        """
        all_novels = []

        for genre in genres:
            try:
                self.logger.info(f"Crawling {genre} genre from {self.platform_name}")
                novels = await self.crawl_genre(
                    genre=genre,
                    limit=limit_per_genre,
                    include_adult=include_adult
                )
                all_novels.extend(novels)
                self.logger.info(f"Collected {len(novels)} novels from {genre}")
            except Exception as e:
                self.logger.error(f"Error crawling {genre}: {str(e)}")
                continue

        return all_novels

    def log_crawl_summary(self, novels: List[Dict]):
        """Log summary of crawled data."""
        self.logger.info(f"""
        Crawl Summary for {self.platform_name}:
        - Total novels: {len(novels)}
        - Unique authors: {len(set(n['author'] for n in novels))}
        - Timestamp: {datetime.now().isoformat()}
        """)
