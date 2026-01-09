import asyncio
import logging
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class CrawlerClient:
    """
    BeautifulSoup + Playwright Selectors 로 데이터 수집
    """

    def __init__(self, headless: bool = True):
        """
        Initialize the client.

        Args:
            headless: Run browser in headless mode
        """

        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._playwright_context = None

    async def _ensure_browser(self):
        """Ensure browser is initialized"""
        if self.browser is None:
            self._playwright_context = await async_playwright().start()
            self.browser = await self._playwright_context.chromium.launch(
                headless=self.headless
            )
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

    async def create_page(self) -> Page:
        """Create a new page"""
        await self._ensure_browser()
        return await self.context.new_page()

    async def close(self):
        """Close browser and cleanup"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright_context:
            await self._playwright_context.stop()
        
        self.context = None
        self.browser = None
        self._playwright_context = None


    #전통적인 selector 기반 크롤링 (CSS Selector 또는 XPath)
    async def navigate_and_extract(
        self,
        url: str,
        list_selector: str,
        field_selectors: Dict[str, str],
        limit: int = 100,
        pagination_strategy: str = "infinite_scroll",
        next_button_selector: Optional[str] = None,
        wait_time: float = 2.0
    ) -> List[Dict]:
        """
        Args:
            url: 크롤링할 URL
            list_selector: 소설 목록 아이템의 selector
                CSS: "div.novel-item"
                XPath: "xpath://div[@class='novel-item']"
            field_selectors: 각 필드를 추출할 selector 딕셔너리
                CSS 예: {
                    "title": "h3.title",
                    "author": "span.author",
                    "url": "a.link@href"
                }
                XPath 예: {
                    "title": "xpath:.//h3[@class='title']",
                    "author": "xpath:.//span[@class='author']",
                    "url": "xpath:.//a/@href"
                }
            limit: 최대 수집 개수
            pagination_strategy: "infinite_scroll" 또는 "pagination"
            next_button_selector: 페이지네이션 버튼 selector
            wait_time: 페이지 로딩 대기 시간
        """
        page = await self.create_page()
        results = []

        try:
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(wait_time)

            if pagination_strategy == "infinite_scroll":
                results = await self._extract_with_scroll(
                    page, list_selector, field_selectors, limit, wait_time
                )
            else:
                results = await self._extract_with_pagination(
                    page, list_selector, field_selectors, limit,
                    next_button_selector or "a.next, button.next, .pagination .next",
                    wait_time
                )

        except Exception as e:
            logger.error(f"크롤링 실패: {str(e)}")
        finally:
            await page.close()

        logger.info(f"Extracted {len(results)} items")
        return results

    # 무한 스크롤 방식으로 데이터 추출
    async def _extract_with_scroll(
        self,
        page: Page,
        list_selector: str,
        field_selectors: Dict[str, str],
        limit: int,
        wait_time: float
    ) -> List[Dict]:
        results = []
        previous_count = 0
        no_new_items_count = 0
        max_no_new_items = 3

        while len(results) < limit:
            # 현재 페이지의 HTML 가져오기
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # 목록 아이템 찾기 (CSS 또는 XPath)
            items = self._select_elements(soup, list_selector)
            logger.debug(f"Found {len(items)} items on page")

            # 각 아이템에서 데이터 추출
            for item in items:
                if len(results) >= limit:
                    break

                data = {}
                for field, selector in field_selectors.items():
                    data[field] = self._extract_field(item, selector)

                # 중복 체크 (URL 기준)
                if data.get("url") and not any(r.get("url") == data["url"] for r in results):
                    results.append(data)

            # 새로운 아이템이 없으면 카운트 증가
            if len(results) == previous_count:
                no_new_items_count += 1
                if no_new_items_count >= max_no_new_items:
                    logger.info("더 이상 새로운 아이템이 없습니다.")
                    break
            else:
                no_new_items_count = 0

            previous_count = len(results)

            # 스크롤 다운
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(wait_time)

        return results[:limit]

    #페이지네이션 방식으로 데이터 추출
    async def _extract_with_pagination(
        self,
        page: Page,
        list_selector: str,
        field_selectors: Dict[str, str],
        limit: int,
        next_button_selector: str,
        wait_time: float
    ) -> List[Dict]:
        results = []
        page_num = 1

        while len(results) < limit:
            logger.debug(f"Extracting page {page_num}")

            # 현재 페이지 데이터 추출
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            items = self._select_elements(soup, list_selector)

            for item in items:
                if len(results) >= limit:
                    break

                data = {}
                for field, selector in field_selectors.items():
                    data[field] = self._extract_field(item, selector)

                if data.get("url") and not any(r.get("url") == data["url"] for r in results):
                    results.append(data)

            if len(results) >= limit:
                break

            # 다음 페이지 버튼 찾기
            try:
                next_button = await page.query_selector(next_button_selector)
                if next_button and await next_button.is_visible():
                    await next_button.click()
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(wait_time)
                    page_num += 1
                else:
                    logger.info("다음 페이지 버튼을 찾을 수 없습니다.")
                    break
            except Exception as e:
                logger.warning(f"페이지 이동 실패: {str(e)}")
                break

        return results[:limit]


    #CSS Selector 또는 XPath로 여러 요소 선택
    def _select_elements(self, soup, selector: str) -> list:
        """
        CSS Selector 또는 XPath로 여러 요소 선택

        Args:
            soup: BeautifulSoup object
            selector: CSS selector 또는 "xpath:..." 형식의 XPath

        Returns:
            선택된 요소들의 리스트
        """
        if selector.startswith("xpath:"):
            # XPath 방식
            from lxml import html as lxml_html

            xpath_expr = selector[6:]
            html_str = str(soup)
            tree = lxml_html.fromstring(html_str)

            try:
                elements = tree.xpath(xpath_expr)
                # lxml 요소를 BeautifulSoup 요소로 변환
                from bs4 import BeautifulSoup as BS
                return [BS(lxml_html.tostring(el), 'html.parser') for el in elements if hasattr(el, 'tag')]
            except Exception as e:
                logger.warning(f"XPath selection failed: {xpath_expr}, error: {e}")
                return []
        else:
            # CSS Selector 방식
            return soup.select(selector)

    #selector로 필드 추출
    def _extract_field(self, element, selector: str) -> Any:
        """
        selector 형식:
        CSS Selector:
        - "div.class" : 텍스트 추출
        - "a@href" : 속성 추출
        - "img@src" : 이미지 src 추출
        - "span.tag[multiple]" : 여러 개 추출 (리스트 반환)

        XPath:
        - "xpath://div[@class='title']" : XPath로 텍스트 추출
        - "xpath://a/@href" : XPath로 속성 추출
        - "xpath://span[@class='tag'][multiple]" : XPath로 여러 개 추출
        """
        # XPath 방식
        if selector.startswith("xpath:"):
            xpath_expr = selector[6:]  # "xpath:" 제거
            return self._extract_by_xpath(element, xpath_expr)

        # CSS Selector 방식 (기존)
        # 여러 개 추출
        if "[multiple]" in selector:
            selector = selector.replace("[multiple]", "")
            elements = element.select(selector)
            return [el.get_text(strip=True) for el in elements]

        # 속성 추출
        if "@" in selector:
            css_selector, attr = selector.split("@", 1)
            el = element.select_one(css_selector)
            return el.get(attr, "").strip() if el else ""

        # 텍스트 추출
        el = element.select_one(selector)
        return el.get_text(strip=True) if el else ""

    #XPath로 필드 추출
    def _extract_by_xpath(self, element, xpath: str) -> Any:
        """
        Args:
            element: BeautifulSoup element
            xpath: XPath 표현식

        Returns:
            추출된 값 (문자열 또는 리스트)
        """
        from lxml import etree, html as lxml_html

        # BeautifulSoup을 lxml로 변환
        html_str = str(element)
        tree = lxml_html.fromstring(html_str)

        # 여러 개 추출
        if "[multiple]" in xpath:
            xpath = xpath.replace("[multiple]", "")
            results = tree.xpath(xpath)

            # 텍스트 노드인 경우
            if results and isinstance(results[0], str):
                return [str(r).strip() for r in results]
            # 요소 노드인 경우
            else:
                return [el.text_content().strip() if hasattr(el, 'text_content') else str(el).strip()
                        for el in results]

        # 단일 추출
        try:
            result = tree.xpath(xpath)

            if not result:
                return ""

            # 첫 번째 결과만 사용
            result = result[0]

            # 속성 값인 경우 (문자열)
            if isinstance(result, str):
                return result.strip()

            # 요소 노드인 경우
            if hasattr(result, 'text_content'):
                return result.text_content().strip()

            return str(result).strip()

        except Exception as e:
            logger.warning(f"XPath extraction failed: {xpath}, error: {e}")
            return ""

    #상세 페이지 정보 추출
    async def extract_detail_page(
        self,
        url: str,
        field_selectors: Dict[str, str],
        wait_time: float = 1.0,
        tab_selector: Optional[str] = None,
        wait_after_tab_click: float = 1.0
    ) -> Dict:
        """
        Args:
            url: 상세 페이지 URL
            field_selectors: 추출할 필드의 selector 딕셔너리
            wait_time: 페이지 로딩 대기 시간
            tab_selector: 클릭해야 할 탭의 selector (예: "button[data-tab='info']")
            wait_after_tab_click: 탭 클릭 후 대기 시간
        """
        page = await self.create_page()
        result = {}

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(wait_time)

            # 탭 클릭이 필요한 경우
            if tab_selector:
                try:
                    tab = await page.query_selector(tab_selector)
                    if tab and await tab.is_visible():
                        await tab.click()
                        # 탭 클릭 후 콘텐츠 로딩 대기
                        await asyncio.sleep(wait_after_tab_click)
                        await page.wait_for_load_state("networkidle", timeout=10000)
                        logger.debug(f"Clicked tab: {tab_selector}")
                    else:
                        logger.debug(f"Tab not found or not visible: {tab_selector}")
                except Exception as e:
                    logger.warning(f"Failed to click tab {tab_selector}: {str(e)}")

            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')

            for field, selector in field_selectors.items():
                result[field] = self._extract_field(soup, selector)

        except Exception as e:
            logger.error(f"상세 페이지 추출 실패 ({url}): {str(e)}")
        finally:
            await page.close()

        return result

    #사이트 로그인
    async def login_to_site(
        self,
        url: str,
        username: str,
        password: str,
        username_selector: str = "input[type='text'], input[type='email']",
        password_selector: str = "input[type='password']",
        login_button_selector: str = "button[type='submit']"
    ) -> bool:
        """
        Args:
            url: 로그인 페이지 URL
            username: 사용자 이름
            password: 비밀번호
            username_selector: 아이디 입력 필드 selector
            password_selector: 비밀번호 입력 필드 selector
            login_button_selector: 로그인 버튼 selector
        """
        page = await self.create_page()

        try:
            logger.info(f"Attempting login to {url}")
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(1)

            # 입력 필드 채우기
            await page.fill(username_selector, username)
            await page.fill(password_selector, password)

            # 로그인 버튼 클릭
            await page.click(login_button_selector)
            await page.wait_for_load_state("networkidle")

            # 로그인 성공 여부 확인 (URL 변경 체크)
            current_url = page.url
            success = current_url != url

            logger.info(f"Login {'successful' if success else 'failed'}")
            return success

        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
        finally:
            await page.close()

    def is_available(self) -> bool:
        """Check if crawler is available"""
        return True
