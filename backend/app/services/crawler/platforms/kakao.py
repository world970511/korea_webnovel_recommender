"""
Kakao Page Crawler
"""

import asyncio
from typing import List, Dict, Optional
from ..base import BaseCrawler
from ....config import settings

class KakaoPageCrawler(BaseCrawler):
    """
    카카오 페이지 크롤러.

    CSS Selector를 사용하여 목록 페이지와 상세 페이지에서 정보를 수집합니다.
    """

    BASE_URL = "https://page.kakao.com"
    NOVEL_ALL_CATEGORY_URL = "https://page.kakao.com/menu/10011/screen/84"  # 웹소설 전체
    NOVEL_ALL_CATEGORY_NEW = "https://page.kakao.com/menu/10011/screen/101"  # 웹소설 신작
    LOGIN_URL = "https://accounts.kakao.com/login"

    # CSS Selectors - 카카오페이지 실제 HTML 구조에 맞춤
    SELECTORS = {
        "list": {
            # 무한 스크롤 리스트 내의 각 작품 링크 (href에 /content/ 포함)
            "item": "a.cursor-pointer[href*='/content/']",

            # 작품 제목 (font-small1 클래스를 가진 div)
            "title": "div.font-small1",

            # 작품 상세 페이지 URL
            "url": "xpath:.//@href",
        },
        "detail": {
            # 장르: <span class="break-all align-middle">현판</span>
            "genre": "span.break-all.align-middle",

            # 작가: <span class="font-small2 mb-6pxr text-ellipsis text-el-70 opacity-70 break-word-anywhere line-clamp-2">글먼지</span>
            "author": "span.font-small2.mb-6pxr.text-ellipsis.text-el-70.opacity-70",

            # 줄거리: <span class="font-small1 mb-8pxr block whitespace-pre-wrap break-words text-el-70">
            "description": "span.font-small1.mb-8pxr.block.whitespace-pre-wrap.break-words.text-el-70",

            # 키워드: <span class="font-small2-bold text-ellipsis text-el-70 line-clamp-1">#성장</span> (복수)
            "keywords": "xpath://span[contains(@class, 'font-small2-bold') and contains(text(), '#')][multiple]",
        }
    }

    # 정보 탭 selector (카카오 페이지는 상세 페이지에서 정보 탭을 클릭해야 키워드 등이 보임)
    INFO_TAB_SELECTOR = "xpath://div[contains(@data-t-obj, '\"copy\":\"정보\"')]"

    def __init__(self, crawler_client):
        """Initialize Kakao Page crawler."""
        super().__init__(crawler_client, "kakao_page")
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
            limit: 수집소설 수
            include_adult: 성인 콘텐츠 포함 여부

        Returns:
            수집된 소설 리스트
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

        # 1단계: 목록 페이지에서 기본 정보 수집 (무한 스크롤)
        novels_basic = await self.client.navigate_and_extract(
            url=url,
            list_selector=self.SELECTORS["list"]["item"],
            field_selectors={
                "title": self.SELECTORS["list"]["title"],
                "url": self.SELECTORS["list"]["url"],
            },
            limit=limit,
            pagination_strategy="infinite_scroll",
            wait_time=2.0
        )

        # 2단계: 각 소설의 상세 페이지의 정보탭을 방문하여 추가 정보 수집 (병렬 처리)
        async def fetch_detail(novel_basic):
            """단일 상세 페이지 수집"""
            detail_url = novel_basic.get("url")
            if not detail_url:
                return None

            # 상대 경로를 절대 경로로 변환
            if detail_url.startswith("/"):
                detail_url = f"https://page.kakao.com{detail_url}"

            try:
                detail_data = await self.client.extract_detail_page(
                    url=detail_url,
                    field_selectors=self.SELECTORS["detail"],
                    wait_time=1.0,
                    tab_selector=self.INFO_TAB_SELECTOR,  # 정보 탭 클릭
                    wait_after_tab_click=1.5
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

                # 장르를 키워드에 병합
                novel["keywords"].extend(novel.get("genre", []))

                return self.normalize_novel_data(novel)
            except Exception as e:
                self.logger.warning(f"Failed to extract detail page {detail_url}: {str(e)}")
                return None

        # 병렬로 상세 페이지 수집 (최대 5개씩 동시 처리)
        batch_size = 5
        novels = []
        for i in range(0, len(novels_basic), batch_size):
            batch = novels_basic[i:i+batch_size]
            batch_results = await asyncio.gather(*[fetch_detail(novel) for novel in batch])
            novels.extend([novel for novel in batch_results if novel is not None])

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
            limit: 수집할 소설 수
            include_adult: 성인 콘텐츠 포함 여부

        Returns:
            수집된 소설 리스트
        """
        if include_adult and not self.is_logged_in:
            self.logger.warning("Adult content requires login")
            if settings.kakao_username and settings.kakao_password:
                await self.login(settings.kakao_username, settings.kakao_password)
            else:
                self.logger.error("Kakao credentials not configured")
                include_adult = False

        url = self.NOVEL_ALL_CATEGORY_NEW
        self.logger.info(f"Crawling new releases from Kakao Page: {url}")

        # 목록 페이지에서 기본 정보 수집 (제목과 URL만)
        novels_basic = await self.client.navigate_and_extract(
            url=url,
            list_selector=self.SELECTORS["list"]["item"],
            field_selectors={
                "title": self.SELECTORS["list"]["title"],
                "url": self.SELECTORS["list"]["url"],
            },
            limit=limit,
            pagination_strategy="infinite_scroll",
            wait_time=2.0
        )

        # 상세 페이지 정보 수집 (병렬 처리)
        async def fetch_detail(novel_basic):
            """단일 상세 페이지 수집"""
            detail_url = novel_basic.get("url")
            if not detail_url:
                return None

            if detail_url.startswith("/"):
                detail_url = f"https://page.kakao.com{detail_url}"

            try:
                detail_data = await self.client.extract_detail_page(
                    url=detail_url,
                    field_selectors=self.SELECTORS["detail"],
                    wait_time=1.0,
                    tab_selector=self.INFO_TAB_SELECTOR,  # 정보 탭 클릭
                    wait_after_tab_click=1.5
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

                return self.normalize_novel_data(novel)
            except Exception as e:
                self.logger.warning(f"Failed to extract detail page {detail_url}: {str(e)}")
                return None

        # 병렬로 상세 페이지 수집 (최대 5개씩 동시 처리)
        batch_size = 5
        novels = []
        for i in range(0, len(novels_basic), batch_size):
            batch = novels_basic[i:i+batch_size]
            batch_results = await asyncio.gather(*[fetch_detail(novel) for novel in batch])
            novels.extend([novel for novel in batch_results if novel is not None])

        self.log_crawl_summary(novels)
        return novels

    async def login(self, username: str, password: str) -> bool:
        """
        카카오에 로그인

        Args:
            username: 카카오 계정 사용자 이름/이메일
            password: 카카오 계정 비밀번호

        Returns:
            성공 여부
        """
        try:
            self.logger.info(f"카카오 로그인 시도: {username}")

            success = await self.client.login_to_site(
                url=self.LOGIN_URL,
                username=username,
                password=password,
                username_selector="input[name='loginId']",
                password_selector="input[name='password']",
                login_button_selector="button[type='submit']"
            )

            self.is_logged_in = success
            return success

        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False
