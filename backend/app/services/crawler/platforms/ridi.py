"""
Ridibooks Crawler

Handles crawling from Ridibooks (ridibooks.com)
which requires genre navigation through menus and categories.
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
    NOVEL_URL = "https://ridibooks.com/category/books/4000"  # Novel category
    LOGIN_URL = "https://ridibooks.com/account/login"

    # Genre mappings (Ridibooks category IDs)
    GENRE_MAP = {
        "판타지": "4100",
        "현대판타지": "4110",
        "로맨스": "4200",
        "로맨스판타지": "4210",
        "무협": "4300",
        "미스터리": "4400",
        "라이트노벨": "4500",
        "BL": "4600",
    }

    def __init__(self, skyvern_client):
        """Initialize Ridibooks crawler."""
        super().__init__(skyvern_client, "ridibooks")
        self.is_logged_in = False

    async def crawl_genre(
        self,
        genre: str,
        limit: int = 20,
        include_adult: bool = False
    ) -> List[Dict]:
        """
        Crawl novels from Ridibooks by genre.

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
        genre_url = f"{self.BASE_URL}/category/books/{category_id}"

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
        리디북스 {genre} 카테고리에서 웹소설을 수집하세요.

        단계:
        1. {genre} 장르 카테고리로 이동
        2. 카테고리 메뉴가 있다면 "웹소설" 또는 "판타지 소설" 등 관련 하위 카테고리 탐색
        3. 현재 페이지의 모든 도서 정보 추출
        4. "더보기" 버튼이나 페이지 번호를 클릭하여 다음 페이지로 이동
        5. {limit}개의 소설을 수집할 때까지 3-4 반복

        각 도서마다 수집할 정보:
        - 제목
        - 저자/작가명
        - 도서 설명 (없으면 생략)
        - 상세 페이지 URL
        - 장르/카테고리 태그

        주의사항:
        - 만화나 e북이 아닌 웹소설만 수집
        - 광고나 배너 제외
        - 중복 제목 제거
        {'- 19세 이상 콘텐츠 포함' if include_adult else '- 19세 이상 콘텐츠는 제외'}
        - 각 페이지 로드 후 2초 대기
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
                max_steps=min(25, limit // 3 + 10)
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

    async def crawl_bestsellers(self, limit: int = 20) -> List[Dict]:
        """
        Crawl bestselling novels.

        Args:
            limit: Number of novels to collect

        Returns:
            List of novel dictionaries
        """
        url = f"{self.BASE_URL}/category/books/4000?order=bestseller"
        self.logger.info("Crawling bestsellers from Ridibooks")

        extraction_schema = {
            "title": "베스트셀러 제목",
            "author": "작가",
            "description": "소개",
            "url": "링크",
            "keywords": "장르",
        }

        prompt = f"""
        리디북스 베스트셀러에서 웹소설 {limit}개를 수집하세요.

        베스트셀러 순서대로 도서 정보를 추출하고,
        필요하면 "더보기"를 클릭하여 더 많은 도서를 확인하세요.
        """

        try:
            result = await self.client.extract_data(
                url=url,
                extraction_schema=extraction_schema,
                navigation_steps=[
                    "베스트셀러 정렬 확인",
                    "웹소설 필터 적용 (있는 경우)",
                    "도서 정보 추출"
                ]
            )

            novels = [self.normalize_novel_data(r) for r in result[:limit]]
            for novel in novels:
                if "베스트셀러" not in novel["keywords"]:
                    novel["keywords"].append("베스트셀러")

            self.log_crawl_summary(novels)
            return novels

        except Exception as e:
            self.logger.error(f"Failed to crawl bestsellers: {str(e)}")
            return []

    async def crawl_new_releases(self, limit: int = 20) -> List[Dict]:
        """
        Crawl newly released novels.

        Args:
            limit: Number of novels to collect

        Returns:
            List of novel dictionaries
        """
        url = f"{self.BASE_URL}/category/books/4000?order=recent"
        self.logger.info("Crawling new releases from Ridibooks")

        extraction_schema = {
            "title": "신작 제목",
            "author": "작가",
            "description": "소개",
            "url": "링크",
            "keywords": "장르",
        }

        prompt = f"""
        리디북스 신간 목록에서 웹소설 {limit}개를 수집하세요.

        최신 출간 순서대로 도서 정보를 추출하세요.
        """

        try:
            result = await self.client.extract_data(
                url=url,
                extraction_schema=extraction_schema
            )

            novels = [self.normalize_novel_data(r) for r in result[:limit]]
            for novel in novels:
                if "신작" not in novel["keywords"]:
                    novel["keywords"].append("신작")

            self.log_crawl_summary(novels)
            return novels

        except Exception as e:
            self.logger.error(f"Failed to crawl new releases: {str(e)}")
            return []

    async def search_novels(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search novels by keyword.

        Args:
            query: Search keyword
            limit: Number of results to collect

        Returns:
            List of novel dictionaries
        """
        # URL encode the query
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        url = f"{self.BASE_URL}/search?q={encoded_query}&what=book"

        self.logger.info(f"Searching Ridibooks for: {query}")

        extraction_schema = {
            "title": "검색 결과 제목",
            "author": "작가",
            "description": "설명",
            "url": "링크",
            "keywords": "장르",
        }

        prompt = f"""
        리디북스에서 "{query}" 키워드로 검색한 결과를 수집하세요.

        검색 결과에서 웹소설만 선택하여 {limit}개까지 정보를 추출하세요.
        만화나 이미지북은 제외하세요.
        """

        try:
            result = await self.client.extract_data(
                url=url,
                extraction_schema=extraction_schema
            )

            novels = [self.normalize_novel_data(r) for r in result[:limit]]
            # Add search query as keyword
            for novel in novels:
                if query not in novel["keywords"]:
                    novel["keywords"].append(query)

            self.log_crawl_summary(novels)
            return novels

        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return []
