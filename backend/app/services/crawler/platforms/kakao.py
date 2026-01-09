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

            # 작품 제목: aria-label 속성에서 추출 (작품명이 aria-label의 첫 번째 항목)
            # aria-label="작품, 미친개는 길들여야 제맛이다, ..."
            "title": "div[aria-label]@aria-label",

            # 작품 상세 페이지 URL
            "url": "xpath:.//@href",
        },
        "detail": {
            # 장르: <span class="break-all align-middle">웹소설</span>
            # 더 간단한 셀렉터로 변경 - align-middle만으로도 충분히 특정 가능
            "genre": "span.align-middle",

            # 작가: <span class="font-small2 mb-6pxr text-ellipsis text-el-70 opacity-70 break-word-anywhere line-clamp-2">김시영</span>
            # opacity-70만으로 간소화 (너무 많은 클래스 조합은 취약)
            "author": "span.opacity-70",

            # 줄거리: <span class="font-small1 mb-8pxr block whitespace-pre-wrap break-words text-el-70">
            # whitespace-pre-wrap만으로 간소화 (줄거리는 보통 이 속성 사용)
            "description": "span.whitespace-pre-wrap",

            # 키워드: <span class="font-small2-bold text-ellipsis text-el-70 line-clamp-1">#게임</span> (복수)
            # font-small2-bold로 특정 (# 기호는 텍스트에 포함되므로 필터링은 나중에)
            "keywords": "span.font-small2-bold[multiple]",
        }
    }

    # 정보 탭 selector (카카오 페이지는 상세 페이지에서 정보 탭을 클릭해야 키워드 등이 보임)
    INFO_TAB_SELECTOR = "a[href*='tab_type=about']"

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

        # aria-label에서 제목 파싱: "작품, 제목, 플랫폼, ..." -> "제목"
        for novel in novels_basic:
            aria_label = novel.get("title", "")
            if aria_label and "," in aria_label:
                parts = aria_label.split(",")
                if len(parts) >= 2:
                    novel["title"] = parts[1].strip()
                else:
                    novel["title"] = ""
            else:
                novel["title"] = ""

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
                    wait_time=2.0,
                    tab_selector=self.INFO_TAB_SELECTOR,  # 정보 탭 클릭
                    wait_after_tab_click=1.5
                )

                # 디버그: 추출된 상세 데이터 확인
                self.logger.debug(f"Detail data from {detail_url}: {detail_data}")

                # 병합
                novel = {
                    "title": novel_basic.get("title", ""),
                    "author": detail_data.get("author", ""),  # ✅ detail_data에서 가져오기
                    "description": detail_data.get("description", ""),
                    "url": detail_url,
                    "keywords": detail_data.get("keywords", []),
                    "platform": self.platform_name
                }

                # keywords가 리스트가 아니면 리스트로 변환
                if isinstance(novel["keywords"], str):
                    novel["keywords"] = [k.strip() for k in novel["keywords"].split(",") if k.strip()]

                # # 기호가 있는 키워드만 필터링 (키워드는 보통 # 기호로 시작)
                if isinstance(novel["keywords"], list):
                    novel["keywords"] = [k.strip() for k in novel["keywords"] if k.strip().startswith("#")]

                # 장르 처리 (detail_data에서 가져오기)
                genre = detail_data.get("genre", "")
                if genre:
                    # genre를 별도 필드로 저장
                    if isinstance(genre, str):
                        novel["genre"] = genre.strip()
                        novel["keywords"].append(genre.strip())
                    elif isinstance(genre, list) and len(genre) > 0:
                        # 여러 장르 중 첫 번째를 메인 장르로 저장
                        novel["genre"] = genre[0].strip()
                        novel["keywords"].extend([g.strip() for g in genre if g.strip()])
                    else:
                        novel["genre"] = ""
                else:
                    novel["genre"] = ""

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

        # aria-label에서 제목 파싱: "작품, 제목, 플랫폼, ..." -> "제목"
        for novel in novels_basic:
            aria_label = novel.get("title", "")
            if aria_label and "," in aria_label:
                parts = aria_label.split(",")
                if len(parts) >= 2:
                    novel["title"] = parts[1].strip()
                else:
                    novel["title"] = ""
            else:
                novel["title"] = ""

        # 디버그: 수집된 기본 데이터 확인
        self.logger.info(f"DEBUG: Collected {len(novels_basic)} items from list page")
        if novels_basic:
            self.logger.info(f"DEBUG: First item sample: {novels_basic[0]}")

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
                    wait_time=2.0,
                    tab_selector=self.INFO_TAB_SELECTOR,  # 정보 탭 클릭
                    wait_after_tab_click=1.5
                )

                # 디버그: 추출된 상세 데이터 확인
                self.logger.debug(f"Detail data from {detail_url}: {detail_data}")

                novel = {
                    "title": novel_basic.get("title", ""),
                    "author": detail_data.get("author", ""),  # ✅ detail_data에서 가져오기
                    "description": detail_data.get("description", ""),
                    "url": detail_url,
                    "keywords": detail_data.get("keywords", []),
                    "platform": self.platform_name
                }

                # keywords가 리스트가 아니면 리스트로 변환
                if isinstance(novel["keywords"], str):
                    novel["keywords"] = [k.strip() for k in novel["keywords"].split(",") if k.strip()]

                # # 기호가 있는 키워드만 필터링 (키워드는 보통 # 기호로 시작)
                if isinstance(novel["keywords"], list):
                    novel["keywords"] = [k.strip() for k in novel["keywords"] if k.strip().startswith("#")]

                # 장르 처리 (detail_data에서 가져오기)
                genre = detail_data.get("genre", "")
                if genre:
                    # genre를 별도 필드로 저장
                    if isinstance(genre, str):
                        novel["genre"] = genre.strip()
                        novel["keywords"].append(genre.strip())
                    elif isinstance(genre, list) and len(genre) > 0:
                        # 여러 장르 중 첫 번째를 메인 장르로 저장
                        novel["genre"] = genre[0].strip()
                        novel["keywords"].extend([g.strip() for g in genre if g.strip()])
                    else:
                        novel["genre"] = ""
                else:
                    novel["genre"] = ""

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
