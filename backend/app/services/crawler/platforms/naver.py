"""
Naver Series Crawler with Traditional CSS Selectors

CSS Selector 기반 전통적인 크롤링 방식
"""

import asyncio
from typing import List, Dict, Optional
from ..base import BaseCrawler
from ....config import settings


class NaverSeriesCrawler(BaseCrawler):
    """
    네이버 시리즈 크롤러.

    CSS Selector를 사용하여 목록 페이지와 상세 페이지에서 정보를 수집합니다.
    """

    BASE_URL = "https://series.naver.com/novel/home.series"
    NOVEL_ALL_CATEGORY_URL = "https://series.naver.com/novel/categoryProductList.series?categoryTypeCode=all"
    NOVEL_ALL_CATEGORY_NEW = "https://series.naver.com/novel/recentList.series"
    LOGIN_URL = "https://nid.naver.com/nidlogin.login"

    # CSS Selectors - 실제 웹 구조에 맞게 수정 필요
    SELECTORS = {
        "list": {
            "item": "li.item",  # TODO: 실제 selector로 수정
            "title": ".title",
            "author": ".author",
            "url": "a@href",
        },
        "detail": {
            "description": ".synopsis",  # TODO: 실제 selector로 수정
            "keywords": ".tag[multiple]",  # 여러 개 추출
            "genre": ".genre",
        }
    }

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

    def __init__(self, crawler_client):
        """Initialize Naver Series crawler."""
        super().__init__(crawler_client, "naver_series")
        self.is_logged_in = False

    async def crawl_all_novels(
        self,
        limit: int = 100,
        include_adult: bool = False,
        **kwargs
    ) -> List[Dict]:
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

        # 1단계: 목록 페이지에서 기본 정보 수집
        novels_basic = await self.client.navigate_and_extract(
            url=url,
            list_selector=self.SELECTORS["list"]["item"],
            field_selectors={
                "title": self.SELECTORS["list"]["title"],
                "author": self.SELECTORS["list"]["author"],
                "url": self.SELECTORS["list"]["url"],
            },
            limit=limit,
            pagination_strategy="pagination",
            next_button_selector="a.next, .pagination .next",
            wait_time=2.0
        )

        # 2단계: 각 소설의 상세 페이지 방문하여 추가 정보 수집
        novels = []
        for novel_basic in novels_basic:
            detail_url = novel_basic.get("url")
            if not detail_url:
                continue

            # 상대 경로를 절대 경로로 변환
            if detail_url.startswith("/"):
                detail_url = f"https://series.naver.com{detail_url}"

            try:
                detail_data = await self.client.extract_detail_page(
                    url=detail_url,
                    field_selectors=self.SELECTORS["detail"],
                    wait_time=1.0
                )

                # 병합
                novel = {
                    "title": novel_basic.get("title", ""),
                    "author": novel_basic.get("author", ""),
                    "description": detail_data.get("description", ""),
                    "url": detail_url,
                    "keywords": detail_data.get("keywords", []),
                    "platform": self.platform_name
                }

                # keywords가 리스트가 아니면 리스트로 변환
                if isinstance(novel["keywords"], str):
                    novel["keywords"] = [k.strip() for k in novel["keywords"].split(",") if k.strip()]

                novels.append(self.normalize_novel_data(novel))
            except Exception as e:
                self.logger.warning(f"Failed to extract detail page {detail_url}: {str(e)}")
                continue

        self.log_crawl_summary(novels)
        return novels

    async def crawl_new_releases(
        self,
        limit: int = 50,
        include_adult: bool = False,
        **kwargs
    ) -> List[Dict]:
        """
        신작 소설 목록을 크롤링

        Args:
            limit: Number of novels to collect
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

        url = self.NOVEL_ALL_CATEGORY_NEW
        self.logger.info(f"Crawling new releases from Naver Series: {url}")

        # 목록 페이지에서 기본 정보 수집
        novels_basic = await self.client.navigate_and_extract(
            url=url,
            list_selector=self.SELECTORS["list"]["item"],
            field_selectors={
                "title": self.SELECTORS["list"]["title"],
                "author": self.SELECTORS["list"]["author"],
                "url": self.SELECTORS["list"]["url"],
            },
            limit=limit,
            pagination_strategy="pagination",
            wait_time=2.0
        )

        # 상세 페이지 정보 수집
        novels = []
        for novel_basic in novels_basic:
            detail_url = novel_basic.get("url")
            if not detail_url:
                continue

            if detail_url.startswith("/"):
                detail_url = f"https://series.naver.com{detail_url}"

            try:
                detail_data = await self.client.extract_detail_page(
                    url=detail_url,
                    field_selectors=self.SELECTORS["detail"],
                    wait_time=1.0
                )

                novel = {
                    "title": novel_basic.get("title", ""),
                    "author": novel_basic.get("author", ""),
                    "description": detail_data.get("description", ""),
                    "url": detail_url,
                    "keywords": detail_data.get("keywords", []),
                    "platform": self.platform_name
                }

                if isinstance(novel["keywords"], str):
                    novel["keywords"] = [k.strip() for k in novel["keywords"].split(",") if k.strip()]

                # 신작 키워드 추가
                if "신작" not in novel["keywords"]:
                    novel["keywords"].append("신작")

                novels.append(self.normalize_novel_data(novel))
            except Exception as e:
                self.logger.warning(f"Failed to extract detail page {detail_url}: {str(e)}")
                continue

        self.log_crawl_summary(novels)
        return novels

    async def login(self, username: str, password: str) -> bool:
        """
        Login to Naver.

        Args:
            username: Naver username
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
                username_selector="input#id",
                password_selector="input#pw",
                login_button_selector="button[type='submit']"
            )

            self.is_logged_in = success
            return success

        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False
