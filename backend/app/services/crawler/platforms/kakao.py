"""
Kakao Page Crawler
"""

import asyncio
from typing import List, Dict, Optional
from backend.app.services.crawler.base import BaseCrawler
from backend.app.config import settings


class KakaoPageCrawler(BaseCrawler):
    """
        카카오 페이지 크롤러.

        목록 페이지의 간단한 정보만 수집하는 대신,
        각 소설의 상세 페이지를 방문하여 완전한 정보를 수집합니다.
    """

    BASE_URL = "https://page.kakao.com"
    NOVEL_ALL_CATEGORY_URL = "https://page.kakao.com/menu/10011/screen/84"  # 웹소설 전체
    NOVEL_ALL_CATEGORY_NEW = "https://page.kakao.com/menu/10011/screen/101"  # 웹소설 신작
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
            if settings.kakao_username and settings.kakao_password:
                await self.login(settings.kakao_username, settings.kakao_password)
            else:
                self.logger.error("Kakao credentials not configured")
                include_adult = False

        url = self.NOVEL_ALL_CATEGORY_URL
        self.logger.info(f"Crawling all novels from Kakao Page: {url}")

        extraction_schema = {
            "title": "웹소설 제목",
            "author": "작가 이름",
            "description": "소설 소개 또는 시놉시스",
            "url": "작품 상세 페이지 링크",
            "keywords": "장르, 태그, 키워드 (쉼표 구분)",
        }

        prompt = f"""
        카카오페이지 전체 웹소설 목록에서 소설을 수집하세요.

        ⭐ 중요: 목록 페이지에는 제목과 이미지만 있습니다. 반드시 각 소설의 상세 페이지에 들어가서 완전한 정보를 수집하세요!

        단계별 작업:

        1. 목록 페이지에서 소설 카드 확인
           - 제목과 작가명 확인
           - 상세 페이지 링크 찾기

        2. 각 소설의 상세 페이지로 이동 (링크 클릭)
           - 완전한 줄거리/시놉시스 수집
           - 태그와 키워드 모두 수집

        3. 목록 페이지로 돌아가기 (뒤로가기)

        4. 다음 소설로 이동하여 2-3 반복

        5. {limit}개 수집할 때까지 계속
           - 무한 스크롤이 적용되어 있습니다. 페이지 맨 아래로 스크롤하여 새로운 콘텐츠를 로드하세요.
           - 스크롤 후 1-2초 대기하여 로딩을 기다리세요.

        수집할 정보:
        - 제목: 정확한 소설 제목
        - 작가: 작가명 또는 필명
        - 소개글: 상세 페이지의 전체 소개글 (필수)
        - URL: 상세 페이지 전체 주소
        - 태그/키워드: 장르 태그나 키워드

        주의사항:
        - 반드시 상세 페이지에 들어가서 정보 수집!
        - 무한 스크롤이므로 천천히 스크롤
        - 각 스크롤 후 1-2초 대기하여 콘텐츠 로딩 시간 확보
        - 광고나 배너 제외
        - 중복 제목 제거
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
                    normalized = self.normalize_novel_data(raw_novel)
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
            if settings.kakao_username and settings.kakao_password:
                await self.login(settings.kakao_username, settings.kakao_password)
            else:
                self.logger.error("Kakao credentials not configured")
                include_adult = False

        url = self.NOVEL_ALL_CATEGORY_NEW
        self.logger.info(f"Crawling new releases from Kakao Page: {url}")

        extraction_schema = {
            "title": "웹소설 제목",
            "author": "작가 이름",
            "description": "소설 소개 또는 시놉시스",
            "url": "작품 상세 페이지 링크",
            "keywords": "장르, 태그, 키워드 (쉼표 구분)",
        }

        prompt = f"""
        카카오페이지 신작 웹소설 목록에서 소설을 수집하세요.

        ⭐ 중요: 목록 페이지에는 제목과 이미지만 있습니다. 반드시 각 소설의 상세 페이지에 들어가서 완전한 정보를 수집하세요!

        단계별 작업:

        1. 신작 탭의 목록 페이지에서 소설 카드 확인
           - 제목과 작가명 확인
           - 상세 페이지 링크 찾기

        2. 각 소설의 상세 페이지로 이동 (링크 클릭)
           - 완전한 줄거리/시놉시스 수집
           - 태그와 키워드 모두 수집

        3. 목록 페이지로 돌아가기 (뒤로가기)

        4. 다음 소설로 이동하여 2-3 반복

        5. 출간 정보가 서버 시간의 날짜보다 이전이면 수집 중단.
           - 무한 스크롤이 적용되어 있습니다. 페이지 맨 아래로 스크롤하여 새로운 콘텐츠를 로드하세요.
           - 스크롤 후 1-2초 대기하여 로딩을 기다리세요.

        수집할 정보:
        - 제목: 정확한 소설 제목
        - 작가: 작가명 또는 필명
        - 소개글: 상세 페이지의 전체 소개글 (필수)
        - URL: 상세 페이지 전체 주소
        - 태그/키워드: 장르 태그나 키워드

        주의사항:
        - 반드시 상세 페이지에 들어가서 정보 수집!
        - 무한 스크롤이므로 천천히 스크롤
        - 각 스크롤 후 1-2초 대기하여 콘텐츠 로딩 시간 확보
        - 광고나 배너 제외
        - 중복 제목 제거
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
                    normalized = self.normalize_novel_data(raw_novel)
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
