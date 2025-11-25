"""
Enhanced Naver Series Crawler with Detail Page Extraction

상세 페이지 방문을 통한 완전한 정보 수집
"""

import asyncio
from typing import List, Dict, Optional
from backend.app.services.crawler.base import BaseCrawler
from backend.app.config import settings


class NaverSeriesCrawler(BaseCrawler):
    """
        네이버 시리즈 크롤러.

        목록 페이지의 간단한 정보만 수집하는 대신,
        각 소설의 상세 페이지를 방문하여 완전한 정보를 수집합니다.
    """

    BASE_URL = "https://series.naver.com/novel/home.series"
    NOVEL_ALL_CATEGORY_URL = "https://series.naver.com/novel/categoryProductList.series?categoryTypeCode=all"
    NOVEL_ALL_CATEGORY_NEW= "https://series.naver.com/novel/recentList.series"
    LOGIN_URL = "https://nid.naver.com/nidlogin.login"

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
        """Initialize enhanced Naver Series crawler."""
        super().__init__(skyvern_client, "naver_series")
        self.is_logged_in = False

    def normalize_novel_data_enhanced(self, raw_data: Dict) -> Dict:
        """
        확장된 필드를 포함한 데이터 정규화.

        Args:
            raw_data: Raw data from Skyvern with enhanced fields
        Returns:
            Normalized novel dictionary with additional metadata
        """
        # 기본 필드
        base_novel = {
            "title": raw_data.get("title", "").strip(),
            "author": raw_data.get("author", "").strip(),
            "description": raw_data.get("description", "").strip(),
            "platform": self.platform_name,
            "url": raw_data.get("url", "").strip(),
            "keywords": self._extract_keywords(raw_data),
        }
        return base_novel

    async def crawl_all_novels(self, limit: int = 100, include_adult: bool = False) -> List[Dict]:
        """
        전체 소설 목록을 크롤링

        Args:
            limit: Number of novels to collect
            include_adult: Whether to include adult content (requires login)

        Returns:
            List of novel dictionaries
        """
        # 성인물 포함 시 로그인 확인
        if include_adult and not self.is_logged_in:
            self.logger.warning("Adult content requires login")
            if settings.naver_username and settings.naver_password:
                await self.login(settings.naver_username, settings.naver_password)
            else:
                self.logger.error("Naver credentials not configured")
                include_adult = False

        url = self.NOVEL_ALL_CATEGORY_URL
        self.logger.info(f"Crawling all novels from Naver Series: {url}")

        extraction_schema = {
            "title": "소설 제목",
            "author": "작가 이름",
            "description": "소설 상세 줄거리 (긴 버전)",
            "url": "소설 상세 페이지 URL",
            "keywords": "장르, 태그, 키워드 (쉼표 구분)",
        }

        prompt = f"""
        네이버 시리즈 전체 소설 목록에서 웹소설을 수집하세요.

        ⭐ 중요: 목록 페이지의 소개글은 잘려있습니다. 반드시 각 소설의 상세 페이지에 들어가서 완전한 정보를 수집하세요!

        단계별 작업:

        1. 목록 페이지에서 소설 카드 확인
           - 제목과 작가명 확인
           - 상세 페이지 링크 찾기

        2. 각 소설의 상세 페이지로 이동 (링크 클릭)
           - 완전한 줄거리/시놉시스 수집 (목록의 잘린 소개글 아님)
           - 태그와 키워드 모두 수집

        3. 목록 페이지로 돌아가기 (뒤로가기)

        4. 다음 소설로 이동하여 2-3 반복

        5. 출간 정보가 서버 시간의 날짜보다 이전이면 수집 중단.
           - "더보기" 버튼이나 페이지 번호를 클릭하여 다음 페이지로 이동

        수집할 정보:
        - 제목: 정확한 소설 제목
        - 작가: 작가명 또는 필명
        - 소개글: 상세 페이지의 전체 소개글 (필수)
        - URL: 상세 페이지 전체 주소
        - 태그/키워드: #로 시작하는 태그, 장르 분류 등 모두

        주의사항:
        - 반드시 상세 페이지에 들어가서 정보 수집!
        - 광고나 배너 무시
        - 중복 제목 제외
        - 신작, 베스트셀러 탭은 제외하고 일반 전체 목록만 수집
        {'- 19세 이상 콘텐츠 포함' if include_adult else '- 19세 이상 콘텐츠는 제외'}
        """

        try:
            result = await self.client.run_task(
                url=url,
                prompt=prompt,
                data_extraction_goal="\n".join([
                    f"{k}: {v}" for k, v in extraction_schema.items()
                ]),
                max_steps=limit * 3
            )

            raw_novels = result.get("extracted_data", [])
            novels = []
            for raw_novel in raw_novels[:limit]:
                try:
                    normalized = self.normalize_novel_data_enhanced(raw_novel)
                    novels.append(normalized)
                except Exception as e:
                    self.logger.warning(f"Failed to normalize novel: {str(e)}")
                    continue

            self.log_crawl_summary(novels)
            return novels

        except Exception as e:
            self.logger.error(f"Failed to crawl all novels: {str(e)}")
            return []

    async def crawl_new_releases(self, limit: int = 50, include_adult: bool = False) -> List[Dict]:
        """
        신작 소설 목록을 크롤링

        Args:
            limit: Number of novels to collect
            include_adult: Whether to include adult content (requires login)

        Returns:
            List of novel dictionaries
        """
        # 성인물 포함 시 로그인 확인
        if include_adult and not self.is_logged_in:
            self.logger.warning("Adult content requires login")
            if settings.naver_username and settings.naver_password:
                await self.login(settings.naver_username, settings.naver_password)
            else:
                self.logger.error("Naver credentials not configured")
                include_adult = False

        url = self.NOVEL_ALL_CATEGORY_NEW
        self.logger.info(f"Crawling new releases from Naver Series: {url}")

        extraction_schema = {
            "title": "소설 제목",
            "author": "작가 이름",
            "description": "소설 상세 줄거리",
            "url": "소설 상세 페이지 URL",
            "keywords": "장르, 태그, 키워드 (쉼표 구분)",
        }

        prompt = f"""
        네이버 시리즈 신작 소설 목록에서 웹소설을 수집하세요.

        ⭐ 중요: 목록 페이지의 소개글은 잘려있습니다. 반드시 각 소설의 상세 페이지에 들어가서 완전한 정보를 수집하세요!

        단계별 작업:

        1. 신작 목록 페이지에서 소설 카드 확인
           - 제목과 작가명 확인
           - 상세 페이지 링크 찾기

        2. 각 소설의 상세 페이지로 이동 (링크 클릭)
           - 완전한 줄거리/시놉시스 수집 (목록의 잘린 소개글 아님)
           - 태그와 키워드 모두 수집

        3. 목록 페이지로 돌아가기 (뒤로가기)

        4. 다음 소설로 이동하여 2-3 반복

        5. {limit}개 수집할 때까지 계속
           -"더보기" 버튼이나 페이지 번호를 클릭하여 다음 페이지로 이동

        수집할 정보:
        - 제목: 정확한 소설 제목
        - 작가: 작가명 또는 필명
        - 소개글: 상세 페이지의 전체 소개글 (필수)
        - URL: 상세 페이지 전체 주소
        - 태그/키워드: #로 시작하는 태그, 장르 분류 등 모두

        주의사항:
        - 반드시 상세 페이지에 들어가서 정보 수집!
        - 광고나 배너 무시
        - 중복 제목 제외
        - 최신 등록순으로 수집
        {'- 19세 이상 콘텐츠 포함' if include_adult else '- 19세 이상 콘텐츠는 제외'}
        """

        try:
            result = await self.client.run_task(
                url=url,
                prompt=prompt,
                data_extraction_goal="\n".join([
                    f"{k}: {v}" for k, v in extraction_schema.items()
                ]),
                max_steps=limit * 3
            )

            raw_novels = result.get("extracted_data", [])
            novels = []
            for raw_novel in raw_novels[:limit]:
                try:
                    normalized = self.normalize_novel_data_enhanced(raw_novel)
                    # Add "신작" keyword
                    if "신작" not in normalized["keywords"]:
                        normalized["keywords"].append("신작")
                    novels.append(normalized)
                except Exception as e:
                    self.logger.warning(f"Failed to normalize novel: {str(e)}")
                    continue

            self.log_crawl_summary(novels)
            return novels

        except Exception as e:
            self.logger.error(f"Failed to crawl new releases: {str(e)}")
            return []

    async def login(self, username: str, password: str) -> bool:
        """Login to Naver."""
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
