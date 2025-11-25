"""
Naver Series Crawler

Handles crawling from Naver Series (series.naver.com)
which uses pagination-based navigation.
"""

import asyncio
from typing import List, Dict, Optional
from backend.app.services.crawler.base import BaseCrawler
from backend.app.config import settings


class NaverSeriesCrawler(BaseCrawler):
    """
    Crawler for Naver Series platform.

    Naver Series uses pagination, so we need to iterate through pages
    by clicking "next page" buttons or page numbers.
    """

    BASE_URL = "https://series.naver.com/novel"
    LOGIN_URL = "https://nid.naver.com/nidlogin.login"

    # Genre mappings (Naver Series genre codes)
    GENRE_MAP = {
        "판타지": "fantasy",
        "현대판타지": "modern_fantasy",
        "로맨스": "romance",
        "로맨스판타지": "romance_fantasy",
        "무협": "martial_arts",
        "BL": "bl",
        "미스터리": "mystery",
        "드라마": "drama",
    }

    def __init__(self, skyvern_client):
        """Initialize Naver Series crawler."""
        super().__init__(skyvern_client, "naver_series")
        self.is_logged_in = False

    async def crawl_genre(
        self,
        genre: str,
        limit: int = 20,
        include_adult: bool = False
    ) -> List[Dict]:
        """
        Crawl novels from Naver Series by genre.

        Args:
            genre: Genre name in Korean (e.g., "판타지", "로맨스")
            limit: Maximum number of novels to collect
            include_adult: Whether to include adult content (requires login)

        Returns:
            List of novel dictionaries
        """
        if include_adult and not self.is_logged_in:
            self.logger.warning("Adult content requires login")
            if settings.naver_username and settings.naver_password:
                await self.login(settings.naver_username, settings.naver_password)
            else:
                self.logger.error("Naver credentials not configured")
                include_adult = False

        # Get genre URL
        genre_code = self.GENRE_MAP.get(genre, "fantasy")
        genre_url = f"{self.BASE_URL}/genre/{genre_code}"

        self.logger.info(f"Starting crawl of {genre} from {genre_url}")

        # Define extraction schema
        extraction_schema = {
            "title": "소설 제목",
            "author": "작가 이름",
            "description": "소설 설명 또는 줄거리",
            "url": "소설 상세 페이지 URL",
            "keywords": "장르, 태그 또는 키워드 (쉼표로 구분)",
        }

        # Build prompt for Skyvern
        prompt = f"""
        네이버 시리즈 {genre} 장르 페이지에서 소설 목록을 수집하세요.

        단계:
        1. 페이지에 있는 모든 소설 정보를 추출
        2. 각 소설마다 다음 정보를 수집:
           - 제목
           - 작가명
           - 소설 설명/줄거리
           - 상세 페이지 URL
           - 태그나 키워드

        3. {limit}개의 소설을 수집할 때까지 "다음 페이지" 버튼을 클릭하여 계속 수집
        4. 페이지가 더 이상 없으면 중단

        주의사항:
        - 광고나 배너는 무시
        - 중복 제목은 제외
        {'- 19세 이상 콘텐츠 포함' if include_adult else '- 19세 이상 콘텐츠는 제외'}
        """

        try:
            # Run Skyvern task
            result = await self.client.extract_data(
                url=genre_url,
                extraction_schema=extraction_schema,
                navigation_steps=[
                    "페이지 로드 대기",
                    f"{limit}개 소설 수집까지 페이지네이션 진행"
                ]
            )

            # Normalize and filter results
            novels = []
            for raw_novel in result[:limit]:
                try:
                    normalized = self.normalize_novel_data(raw_novel)
                    # Add genre to keywords
                    if genre not in normalized["keywords"]:
                        normalized["keywords"].append(genre)
                    novels.append(normalized)
                except Exception as e:
                    self.logger.warning(f"Failed to normalize novel: {str(e)}")
                    continue

            self.log_crawl_summary(novels)
            return novels

        except Exception as e:
            self.logger.error(f"Failed to crawl {genre}: {str(e)}")
            return []

    async def login(self, username: str, password: str) -> bool:
        """
        Login to Naver.

        Args:
            username: Naver username or email
            password: Naver password

        Returns:
            True if login successful
        """
        try:
            self.logger.info(f"Attempting Naver login for {username}")

            success = await self.client.login_to_site(
                url=self.LOGIN_URL,
                username=username,
                password=password,
                username_field_desc="아이디 입력란",
                password_field_desc="비밀번호 입력란",
                login_button_desc="로그인 버튼"
            )

            self.is_logged_in = success
            return success

        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False

    async def crawl_top_novels(self, limit: int = 20) -> List[Dict]:
        """
        Crawl top/popular novels from the main page.

        Args:
            limit: Number of novels to collect

        Returns:
            List of novel dictionaries
        """
        self.logger.info("Crawling top novels from Naver Series")

        extraction_schema = {
            "title": "소설 제목",
            "author": "작가 이름",
            "description": "소설 설명",
            "url": "소설 URL",
            "keywords": "장르 태그",
        }

        prompt = f"""
        네이버 시리즈 메인 페이지에서 인기 소설 {limit}개를 수집하세요.

        상위 랭킹이나 추천 섹션에서 소설 정보를 추출하고,
        각 소설의 제목, 작가, 설명, URL, 장르를 가져오세요.
        """

        try:
            result = await self.client.extract_data(
                url=self.BASE_URL,
                extraction_schema=extraction_schema
            )

            novels = [self.normalize_novel_data(r) for r in result[:limit]]
            self.log_crawl_summary(novels)
            return novels

        except Exception as e:
            self.logger.error(f"Failed to crawl top novels: {str(e)}")
            return []
