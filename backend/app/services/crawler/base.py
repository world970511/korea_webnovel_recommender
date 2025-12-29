"""
Base Crawler Class

모든 플랫폼의 베이스 크롤러
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):

    def __init__(self, crawler_client, platform_name: str):
        """
        크롤러 초기화

        Args:
            crawler_client: 크롤러 클라이언트
            platform_name: 플랫폼 이름
        """
        self.client = crawler_client
        self.platform_name = platform_name
        self.logger = logging.getLogger(f"{__name__}.{platform_name}")

    @abstractmethod
    async def crawl_all_novels(
        self,
        limit: int = 100,
        include_adult: bool = False,
        **kwargs
    ) -> List[Dict]:
        """
        플랫폼에서 모든 소설을 수집

        Args:
            limit: 수집할 소설의 최대 수
            include_adult: 성인 콘텐츠 포함 여부
            **kwargs: 플랫폼별 추가 매개변수

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

    async def crawl_new_releases(
        self,
        limit: int = 50,
        include_adult: bool = False,
        **kwargs
    ) -> List[Dict]:
        """
        플랫폼에서 새로운 소설을 수집

        Args:
            limit: 수집할 소설의 최대 수
            include_adult: 성인 콘텐츠 포함 여부
            **kwargs: 플랫폼별 추가 매개변수

        Returns:
            List of novel dictionaries
        """
        self.logger.warning(
            f"{self.platform_name} does not have specific new_releases crawler. "
            "Falling back to crawl_all_novels."
        )
        return await self.crawl_all_novels(limit=limit, include_adult=include_adult, **kwargs)

    async def crawl_genre(
        self,
        genre: str,
        limit: int = 20,
        include_adult: bool = False
    ) -> List[Dict]:
        """
        플랫폼에서 특정 장르의 소설을 수집

        Args:
            genre: 장르 이름 (e.g., "판타지", "로맨스", "무협")
            limit: 수집할 소설의 최대 수
            include_adult: 성인 콘텐츠 포함 여부

        Returns:
            List of novel dictionaries
        """
        self.logger.info(f"Using crawl_all_novels with genre={genre}")
        return await self.crawl_all_novels(
            limit=limit,
            include_adult=include_adult,
            genre=genre
        )

    @abstractmethod
    async def login(self, username: str, password: str) -> bool:
        """
        플랫폼에 로그인 (성인 콘텐츠를 위해 필요)

        Args:
            username: 플랫폼 사용자 이름
            password: 플랫폼 비밀번호

        Returns:
            성공 여부
        """
        pass

    def normalize_novel_data(self, raw_data: Dict) -> Dict:
        """
        크롤링된 데이터를 표준 형식으로 정규화

        Args:
            raw_data: 크롤링된 데이터

        Returns:
            정규화된 소설 데이터
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
        크롤링된 데이터에서 키워드를 추출하고 정리

        Args:
            raw_data: 크롤링된 데이터

        Returns:
            정리된 키워드 리스트
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
        여러 장르의 소설을 수집

        Args:
            genres: 장르 이름 리스트
            limit_per_genre: 장르별로 수집할 소설의 최대 수
            include_adult: 성인 콘텐츠 포함 여부

        Returns:
            모든 장르의 소설 리스트
        """
        all_novels = []

        for genre in genres:
            try:
                self.logger.info(f"Crawling {genre} genre from {self.platform_name}")
                # Call crawl_all_novels with genre parameter
                novels = await self.crawl_all_novels(
                    limit=limit_per_genre,
                    include_adult=include_adult,
                    genre=genre
                )
                all_novels.extend(novels)
                self.logger.info(f"Collected {len(novels)} novels from {genre}")
            except Exception as e:
                self.logger.error(f"Error crawling {genre}: {str(e)}")
                continue

        return all_novels

    def log_crawl_summary(self, novels: List[Dict]):
        """
        크롤링된 데이터의 요약을 로그에 기록

        Args:
            novels: 크롤링된 소설 리스트
        """
        self.logger.info(f"""
        Crawl Summary for {self.platform_name}:
        - Total novels: {len(novels)}
        - Unique authors: {len(set(n['author'] for n in novels))}
        - Timestamp: {datetime.now().isoformat()}
        """)