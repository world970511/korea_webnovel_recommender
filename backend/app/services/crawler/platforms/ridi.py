
"""
Ridi Crawler
"""

import asyncio
from typing import List, Dict, Optional
from backend.app.services.crawler.base import BaseCrawler
from backend.app.config import settings


class RidibooksCrawler(BaseCrawler):
    """
    Crawler for Ridibooks platform.

    Ridibooks requires navigating through genre menus and categories.
    Novels are not in a single list but organized hierarchically.
    """

    BASE_URL = "https://ridibooks.com"
    NOVEL_ALL_BASE_URL = "https://ridibooks.com/category/books/"  # 각 장르별 전체 페이지 BaseURL 마지막에 장르 ID를 붙여 이동
    NOVEL_NEW_BASE_URL = "https://ridibooks.com/category/new-releases/"# 각 장르별 신작 페이지 BaseURL 마지막에 장르 ID를 붙여 이동
    LOGIN_URL = "https://ridibooks.com/account/login"

    # Genre mappings (Ridibooks category IDs)
    GENRE_MAP = {
        "로맨스": "1650",
        "로맨스판타지": "6050",
        "판타지": "1750",
        "BL": "4150",
    }

    def __init__(self, skyvern_client):
        """Initialize Ridibooks crawler."""
        super().__init__(skyvern_client, "ridibooks")
        self.is_logged_in = False

    async def crawl_all_novels(
        self,
        genre: str,
        limit: int = 20,
        include_adult: bool = False
    ) -> List[Dict]:
        """
        각 장르 링크에 따라 데이터 수집

        Args:
            genre: Genre name in Korean
            limit: Maximum number of novels to collect
            include_adult: Whether to include adult content (requires login)

        Returns:
            List of novel dictionaries
        """
        if include_adult and not self.is_logged_in:
            self.logger.warning("Adult content requires login")
            if settings.ridi_username and settings.ridi_password:
                await self.login(settings.ridi_username, settings.ridi_password)
            else:
                self.logger.error("Ridibooks credentials not configured")
                include_adult = False

        # Get genre category ID
        category_id = self.GENRE_MAP.get(genre, "4100")
        genre_url = f"{self.NOVEL_ALL_BASE_URL}{category_id}"

        self.logger.info(f"Starting crawl of {genre} from {genre_url}")

        # Define extraction schema
        extraction_schema = {
            "title": "도서 제목",
            "author": "저자 또는 작가 이름",
            "description": "도서 소개 또는 시놉시스",
            "url": "도서 상세 페이지 링크",
            "keywords": "장르, 태그, 분류 (쉼표 구분)",
        }

        # Build prompt for genre navigation
        prompt = f"""
        리디북스 {genre} 카테고리(전체 목록)에서 웹소설을 수집하세요.

        ⭐ 중요: 각 소설마다 상세 페이지에 들어가서 완전한 정보를 수집하세요!

        단계별 작업:

        1. {genre} 장르 카테고리 페이지 진입
           - '전체' 탭이 선택되어 있는지 확인 (URL 확인)

        2. 목록에서 각 소설의 상세 페이지로 이동 (링크 클릭)
           - 완전한 줄거리/시놉시스 수집
           - 태그와 키워드 모두 수집

        3. 목록 페이지로 돌아가기 (뒤로가기)

        4. 다음 소설로 이동하여 2-3 반복

        5. {limit}개 수집할 때까지 계속
           - 페이지 하단의 페이지 번호(1, 2, 3...)나 '다음' 버튼을 클릭하여 이동

        수집할 정보:
        - 제목: 정확한 소설 제목
        - 작가: 작가명 또는 필명
        - 소개글: 상세 페이지의 전체 소개글
        - URL: 상세 페이지 전체 주소
        - 태그/키워드: #로 시작하는 태그, 장르 분류 등 모두

        주의사항:
        - 반드시 상세 페이지에 들어가서 정보 수집!
        - 광고나 배너 무시
        - 중복 제목 제외
        {'- 19세 이상 콘텐츠 포함' if include_adult else '- 19세 이상 콘텐츠는 제외'}
        """

        try:
            # Run Skyvern task with navigation
            result = await self.client.run_task(
                url=genre_url,
                prompt=prompt,
                navigation_goal=f"{genre} 카테고리 탐색 및 웹소설 목록 접근",
                data_extraction_goal="\n".join([
                    f"{k}: {v}" for k, v in extraction_schema.items()
                ]),
                max_steps=min(30, limit // 2 + 15) # Adjust steps based on limit
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
        Login to Ridibooks.

        Args:
            username: Ridibooks username/email
            password: Ridibooks password

        Returns:
            True if login successful
        """
        try:
            self.logger.info(f"Attempting Ridibooks login for {username}")

            success = await self.client.login_to_site(
                url=self.LOGIN_URL,
                username=username,
                password=password,
                username_field_desc="아이디 또는 이메일 입력란",
                password_field_desc="비밀번호 입력란",
                login_button_desc="로그인 버튼"
            )

            self.is_logged_in = success
            return success

        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False

    async def crawl_new_releases(
        self,
        genre: str = "판타지",
        limit: int = 20,
        include_adult: bool = False
    ) -> List[Dict]:
        """
        리디북스 신작 소설 목록을 크롤링

        Args:
            genre: Genre name to crawl new releases for
            limit: Number of novels to collect
            include_adult: Whether to include adult content

        Returns:
            List of novel dictionaries
        """
        if include_adult and not self.is_logged_in:
            self.logger.warning("Adult content requires login")
            if settings.ridi_username and settings.ridi_password:
                await self.login(settings.ridi_username, settings.ridi_password)
            else:
                self.logger.error("Ridibooks credentials not configured")
                include_adult = False

        # Get genre category ID
        category_id = self.GENRE_MAP.get(genre, "1750") # Default to Fantasy if not found
        
        # Construct URL for New Releases in this genre
        # Ridi structure: /category/new-releases/{category_id}
        url = f"{self.NOVEL_NEW_BASE_URL}{category_id}"

        self.logger.info(f"Crawling new releases for {genre} from {url}")

        extraction_schema = {
            "title": "신작 제목",
            "author": "작가",
            "description": "소개",
            "url": "링크",
            "keywords": "장르",
        }

        prompt = f"""
        리디북스 {genre} 카테고리의 '신작' 목록에서 웹소설을 수집하세요.

        ⭐ 중요: 각 소설마다 상세 페이지에 들어가서 완전한 정보를 수집하세요!

        단계별 작업:

        1. {genre} 신작 페이지 진입 ({url})

        2. 각 소설의 상세 페이지로 이동 (링크 클릭)
           - 완전한 줄거리/시놉시스 수집
           - 태그와 키워드 모두 수집

        3. 목록 페이지로 돌아가기 (뒤로가기)

        4. 다음 소설로 이동하여 2-3 반복

        5. {limit}개 수집할 때까지 계속
           - 페이지 하단의 페이지 번호나 '다음' 버튼 클릭

        수집할 정보:
        - 제목: 정확한 소설 제목
        - 작가: 작가명 또는 필명
        - 소개글: 상세 페이지의 전체 소개글
        - URL: 상세 페이지 전체 주소
        - 태그/키워드: #로 시작하는 태그, 장르 분류 등 모두

        주의사항:
        - 반드시 상세 페이지에 들어가서 정보 수집!
        - 광고나 배너 무시
        - 중복 제목 제외
        - '신작' 뱃지가 있거나 신작 목록에 있는 작품만 대상
        {'- 19세 이상 콘텐츠 포함' if include_adult else '- 19세 이상 콘텐츠는 제외'}
        """

        try:
            result = await self.client.run_task(
                url=url,
                prompt=prompt,
                navigation_goal=f"{genre} 신작 카테고리 탐색 및 웹소설 목록 접근",
                data_extraction_goal="\n".join([
                    f"{k}: {v}" for k, v in extraction_schema.items()
                ]),
                max_steps=min(30, limit // 2 + 15)
            )

            raw_novels = result.get("extracted_data", [])
            
            novels = []
            for raw_novel in raw_novels[:limit]:
                try:
                    normalized = self.normalize_novel_data(raw_novel)
                    if "신작" not in normalized["keywords"]:
                        normalized["keywords"].append("신작")
                    if genre not in normalized["keywords"]:
                        normalized["keywords"].append(genre)
                    novels.append(normalized)
                except Exception as e:
                    self.logger.warning(f"Failed to normalize novel: {str(e)}")
                    continue

            self.log_crawl_summary(novels)
            return novels

        except Exception as e:
            self.logger.error(f"Failed to crawl new releases: {str(e)}")
            return []
```