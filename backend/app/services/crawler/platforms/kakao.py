"""
Kakao Page Crawler

Handles crawling from Kakao Page (page.kakao.com)
which uses infinite scroll navigation.
"""

import asyncio
from typing import List, Dict, Optional
from backend.app.services.crawler.base import BaseCrawler
from backend.app.config import settings


class KakaoPageCrawler(BaseCrawler):
    """
    Crawler for Kakao Page platform.

    Kakao Page uses infinite scroll, requiring repeated scroll-down
    actions to load more content dynamically.
    """

    BASE_URL = "https://page.kakao.com"
    NOVEL_URL = "https://page.kakao.com/menu/10011"  # Novel section
    LOGIN_URL = "https://accounts.kakao.com/login"

    # Genre mappings
    GENRE_MAP = {
        "판타지": "10",
        "현대판타지": "11",
        "로맨스": "20",
        "로맨스판타지": "21",
        "무협": "30",
        "미스터리": "40",
        "드라마": "50",
        "BL": "60",
    }

    def __init__(self, skyvern_client):
        """Initialize Kakao Page crawler."""
        super().__init__(skyvern_client, "kakao_page")
        self.is_logged_in = False

    async def crawl_genre(
        self,
        genre: str,
        limit: int = 20,
        include_adult: bool = False
    ) -> List[Dict]:
        """
        Crawl novels from Kakao Page by genre.

        Args:
            genre: Genre name in Korean
            limit: Maximum number of novels to collect
            include_adult: Whether to include adult content (requires login)

        Returns:
            List of novel dictionaries
        """
        if include_adult and not self.is_logged_in:
            self.logger.warning("Adult content requires login")
            if settings.kakao_username and settings.kakao_password:
                await self.login(settings.kakao_username, settings.kakao_password)
            else:
                self.logger.error("Kakao credentials not configured")
                include_adult = False

        # Get genre code
        genre_code = self.GENRE_MAP.get(genre, "10")
        genre_url = f"{self.BASE_URL}/menu/{genre_code}"

        self.logger.info(f"Starting crawl of {genre} from {genre_url}")

        # Define extraction schema
        extraction_schema = {
            "title": "웹소설 제목",
            "author": "작가 이름 또는 필명",
            "description": "소설 소개 또는 시놉시스",
            "url": "작품 상세 페이지 링크",
            "keywords": "장르, 태그, 키워드 (쉼표 구분)",
        }

        # Build prompt for infinite scroll handling
        prompt = f"""
        카카오페이지 {genre} 장르 페이지에서 웹소설을 수집하세요.

        단계:
        1. 페이지가 로드될 때까지 대기
        2. 현재 화면에 보이는 모든 웹소설 정보 추출
        3. 페이지를 아래로 스크롤하여 새로운 콘텐츠 로드
        4. 새로 나타난 소설 정보 추출
        5. {limit}개의 소설을 수집할 때까지 3-4 단계 반복
        6. 더 이상 새로운 콘텐츠가 로드되지 않으면 중단

        각 소설마다 수집할 정보:
        - 제목
        - 작가명
        - 소설 설명/줄거리
        - 상세 페이지 URL
        - 장르 태그나 키워드

        주의사항:
        - 무한 스크롤이므로 천천히 스크롤
        - 각 스크롤 후 1-2초 대기하여 콘텐츠 로딩 시간 확보
        - 광고나 배너 제외
        - 중복 제목 제거
        {'- 19세 이상 콘텐츠 포함' if include_adult else '- 19세 이상 콘텐츠는 제외'}
        """

        try:
            # Run Skyvern task with infinite scroll
            result = await self.client.run_task(
                url=genre_url,
                prompt=prompt,
                data_extraction_goal="\n".join([
                    f"{k}: {v}" for k, v in extraction_schema.items()
                ]),
                max_steps=min(30, limit // 2 + 10)  # More steps for scrolling
            )

            # Process extracted data
            raw_novels = result.get("extracted_data", [])

            novels = []
            for raw_novel in raw_novels[:limit]:
                try:
                    normalized = self.normalize_novel_data(raw_novel)
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
        Login to Kakao.

        Args:
            username: Kakao account username/email
            password: Kakao account password

        Returns:
            True if login successful
        """
        try:
            self.logger.info(f"Attempting Kakao login for {username}")

            success = await self.client.login_to_site(
                url=self.LOGIN_URL,
                username=username,
                password=password,
                username_field_desc="이메일 또는 전화번호 입력란",
                password_field_desc="비밀번호 입력란",
                login_button_desc="로그인 버튼"
            )

            self.is_logged_in = success
            return success

        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False

    async def crawl_ranking(
        self,
        ranking_type: str = "realtime",
        limit: int = 20
    ) -> List[Dict]:
        """
        Crawl novels from Kakao Page ranking.

        Args:
            ranking_type: Type of ranking ("realtime", "weekly", "monthly")
            limit: Number of novels to collect

        Returns:
            List of novel dictionaries
        """
        ranking_urls = {
            "realtime": f"{self.BASE_URL}/menu/10011?tab=ranking&type=realtime",
            "weekly": f"{self.BASE_URL}/menu/10011?tab=ranking&type=weekly",
            "monthly": f"{self.BASE_URL}/menu/10011?tab=ranking&type=monthly",
        }

        url = ranking_urls.get(ranking_type, ranking_urls["realtime"])
        self.logger.info(f"Crawling {ranking_type} ranking from Kakao Page")

        extraction_schema = {
            "title": "소설 제목",
            "author": "작가 이름",
            "description": "소설 설명",
            "url": "소설 URL",
            "keywords": "장르 태그",
        }

        prompt = f"""
        카카오페이지 {ranking_type} 랭킹에서 상위 {limit}개 웹소설을 수집하세요.

        랭킹 순서대로 소설의 제목, 작가, 설명, URL, 장르를 추출하세요.
        필요하면 스크롤하여 더 많은 랭킹을 확인하세요.
        """

        try:
            result = await self.client.extract_data(
                url=url,
                extraction_schema=extraction_schema,
                navigation_steps=[
                    "랭킹 탭 클릭",
                    f"{ranking_type} 랭킹 선택",
                    "소설 정보 수집"
                ]
            )

            novels = [self.normalize_novel_data(r) for r in result[:limit]]
            self.log_crawl_summary(novels)
            return novels

        except Exception as e:
            self.logger.error(f"Failed to crawl ranking: {str(e)}")
            return []

    async def crawl_completed_novels(self, limit: int = 20) -> List[Dict]:
        """
        Crawl completed (finished) novels.

        Args:
            limit: Number of novels to collect

        Returns:
            List of novel dictionaries
        """
        url = f"{self.BASE_URL}/menu/10011?tab=completed"
        self.logger.info("Crawling completed novels from Kakao Page")

        extraction_schema = {
            "title": "완결 소설 제목",
            "author": "작가",
            "description": "줄거리",
            "url": "링크",
            "keywords": "장르",
        }

        prompt = f"""
        카카오페이지에서 완결된 웹소설 {limit}개를 수집하세요.

        완결 작품 탭에서 소설 정보를 추출하고,
        무한 스크롤로 충분한 개수가 수집될 때까지 스크롤하세요.
        """

        try:
            result = await self.client.extract_data(
                url=url,
                extraction_schema=extraction_schema
            )

            novels = [self.normalize_novel_data(r) for r in result[:limit]]
            # Add "완결" keyword
            for novel in novels:
                if "완결" not in novel["keywords"]:
                    novel["keywords"].append("완결")

            self.log_crawl_summary(novels)
            return novels

        except Exception as e:
            self.logger.error(f"Failed to crawl completed novels: {str(e)}")
            return []
