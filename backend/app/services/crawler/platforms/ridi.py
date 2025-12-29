"""
Ridi Crawler with Traditional CSS Selectors

CSS Selector 기반 전통적인 크롤링 방식
"""

import asyncio
from typing import List, Dict, Optional
from ..base import BaseCrawler
from ....config import settings


class RidibooksCrawler(BaseCrawler):
    """
    리디북스 크롤러.

    CSS Selector를 사용하여 장르별 목록 페이지와 상세 페이지에서 정보를 수집합니다.
    """

    BASE_URL = "https://ridibooks.com"
    NOVEL_ALL_BASE_URL = "https://ridibooks.com/category/books/"  # 각 장르별 전체 페이지 BaseURL
    NOVEL_NEW_BASE_URL = "https://ridibooks.com/category/new-releases/"  # 각 장르별 신작 페이지 BaseURL
    LOGIN_URL = "https://ridibooks.com/account/login"

    # CSS Selectors - 실제 웹 구조에 맞게 수정 필요
    SELECTORS = {
        "list": {
            "item": ".book-item",  # TODO: 실제 selector로 수정
            "title": ".title",
            "author": ".author",
            "url": "a@href",
        },
        "detail": {
            "description": ".book-description",  # TODO: 실제 selector로 수정
            "keywords": ".tag[multiple]",
            "genre": ".genre",
        }
    }

    # Genre mappings (Ridibooks category IDs)
    GENRE_MAP = {
        "로맨스": "1650",
        "로맨스판타지": "6050",
        "판타지": "1750",
        "BL": "4150",
    }

    def __init__(self, crawler_client):
        """Initialize Ridibooks crawler."""
        super().__init__(crawler_client, "ridibooks")
        self.is_logged_in = False

    async def crawl_all_novels(
        self,
        limit: int = 20,
        include_adult: bool = False,
        **kwargs
    ) -> List[Dict]:
        """
        장르별 전체 소설 목록을 크롤링

        Args:
            limit: Maximum number of novels to collect
            include_adult: Whether to include adult content (requires login)
            **kwargs: Additional parameters (genre required)

        Returns:
            List of novel dictionaries
        """
        genre = kwargs.get("genre", "판타지")

        if include_adult and not self.is_logged_in:
            self.logger.warning("Adult content requires login")
            if settings.ridi_username and settings.ridi_password:
                await self.login(settings.ridi_username, settings.ridi_password)
            else:
                self.logger.error("Ridibooks credentials not configured")
                include_adult = False

        # Get genre category ID
        category_id = self.GENRE_MAP.get(genre, "1750")
        url = f"{self.NOVEL_ALL_BASE_URL}{category_id}"

        self.logger.info(f"Crawling {genre} from Ridibooks: {url}")

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
                detail_url = f"https://ridibooks.com{detail_url}"

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

                # 장르 키워드 추가
                if genre not in novel["keywords"]:
                    novel["keywords"].append(genre)

                novels.append(self.normalize_novel_data(novel))
            except Exception as e:
                self.logger.warning(f"Failed to extract detail page {detail_url}: {str(e)}")
                continue

        self.log_crawl_summary(novels)
        return novels

    async def crawl_new_releases(
        self,
        limit: int = 20,
        include_adult: bool = False,
        **kwargs
    ) -> List[Dict]:
        """
        장르별 신작 소설 목록을 크롤링

        Args:
            limit: Number of novels to collect
            include_adult: Whether to include adult content
            **kwargs: Additional parameters (genre)

        Returns:
            List of novel dictionaries
        """
        genre = kwargs.get("genre", "판타지")

        if include_adult and not self.is_logged_in:
            self.logger.warning("Adult content requires login")
            if settings.ridi_username and settings.ridi_password:
                await self.login(settings.ridi_username, settings.ridi_password)
            else:
                self.logger.error("Ridibooks credentials not configured")
                include_adult = False

        # Get genre category ID
        category_id = self.GENRE_MAP.get(genre, "1750")
        url = f"{self.NOVEL_NEW_BASE_URL}{category_id}"

        self.logger.info(f"Crawling new releases for {genre} from Ridibooks: {url}")

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
            next_button_selector="a.next, .pagination .next",
            wait_time=2.0
        )

        # 상세 페이지 정보 수집
        novels = []
        for novel_basic in novels_basic:
            detail_url = novel_basic.get("url")
            if not detail_url:
                continue

            if detail_url.startswith("/"):
                detail_url = f"https://ridibooks.com{detail_url}"

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

                # 장르 키워드 추가
                if genre not in novel["keywords"]:
                    novel["keywords"].append(genre)

                novels.append(self.normalize_novel_data(novel))
            except Exception as e:
                self.logger.warning(f"Failed to extract detail page {detail_url}: {str(e)}")
                continue

        self.log_crawl_summary(novels)
        return novels

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
                username_selector="input[name='user_id']",
                password_selector="input[name='password']",
                login_button_selector="button[type='submit']"
            )

            self.is_logged_in = success
            return success

        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False
