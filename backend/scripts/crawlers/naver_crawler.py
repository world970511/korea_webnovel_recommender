"""
Naver Series Crawler
"""
import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, parse_qs, urlparse

from .base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class NaverSeriesCrawler(BaseCrawler):
    """Crawler for Naver Series (series.naver.com)"""

    def __init__(self, delay: float = 1.5):
        """Initialize Naver Series crawler"""
        super().__init__(
            platform="네이버시리즈",
            base_url="https://series.naver.com",
            delay=delay
        )
        self.list_url = "https://series.naver.com/novel/categoryProductList.series"
        self._total_pages = None

    def get_total_pages(self) -> int:
        """
        Get total number of pages

        Returns:
            Total page count
        """
        if self._total_pages is not None:
            return self._total_pages

        # Fetch first page to get pagination info
        soup = self.fetch_page(f"{self.list_url}?categoryTypeCode=all&page=1")

        if not soup:
            logger.warning("Could not fetch first page, defaulting to 1 page")
            return 1

        try:
            # Try to find pagination (adjust selector based on actual HTML)
            # Common patterns: .pagination, .paging, etc.
            pagination = soup.find('div', class_='pagination') or \
                        soup.find('div', class_='paging') or \
                        soup.find('div', class_='page_wrap')

            if pagination:
                # Find all page links
                page_links = pagination.find_all('a', href=True)
                max_page = 1

                for link in page_links:
                    href = link.get('href', '')
                    match = re.search(r'page=(\d+)', href)
                    if match:
                        page_num = int(match.group(1))
                        max_page = max(max_page, page_num)

                self._total_pages = max_page
                logger.info(f"Found {max_page} total pages")
                return max_page

            # If no pagination found, check for "last" button
            last_btn = soup.find('a', text=re.compile(r'마지막|끝|last', re.IGNORECASE))
            if last_btn and last_btn.get('href'):
                match = re.search(r'page=(\d+)', last_btn['href'])
                if match:
                    self._total_pages = int(match.group(1))
                    return self._total_pages

        except Exception as e:
            logger.error(f"Error getting total pages: {e}")

        # Default to 100 pages if can't determine
        logger.warning("Could not determine total pages, defaulting to 100")
        self._total_pages = 100
        return 100

    def crawl_list_page(self, page: int = 1) -> List[Dict[str, Any]]:
        """
        Crawl a list page

        Args:
            page: Page number

        Returns:
            List of novel metadata
        """
        url = f"{self.list_url}?categoryTypeCode=all&page={page}"
        soup = self.fetch_page(url)

        if not soup:
            return []

        novels = []

        try:
            # Find novel items (adjust selectors based on actual HTML structure)
            # Common patterns for Naver: .product_item, .work_item, etc.
            items = soup.find_all('li', class_=re.compile(r'product|work|item')) or \
                   soup.find_all('div', class_=re.compile(r'product|work|item'))

            if not items:
                # Fallback: try finding by link pattern
                items = soup.find_all('a', href=re.compile(r'detail\.series\?productNo=\d+'))
                logger.info(f"Using fallback selector, found {len(items)} items")

            for item in items:
                try:
                    novel_data = self._parse_list_item(item)
                    if novel_data:
                        novels.append(novel_data)
                except Exception as e:
                    logger.warning(f"Error parsing item: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error crawling list page {page}: {e}")

        return novels

    def _parse_list_item(self, item) -> Optional[Dict[str, Any]]:
        """
        Parse a single novel item from list page

        Args:
            item: BeautifulSoup element

        Returns:
            Novel metadata dictionary
        """
        try:
            # Find the detail link
            link = item.find('a', href=re.compile(r'detail\.series\?productNo=\d+'))

            if not link:
                return None

            detail_url = urljoin(self.base_url, link['href'])

            # Extract productNo from URL
            parsed = urlparse(detail_url)
            query_params = parse_qs(parsed.query)
            product_no = query_params.get('productNo', [None])[0]

            if not product_no:
                return None

            # Extract basic info from list page
            title_elem = item.find(class_=re.compile(r'title|subject|tit')) or \
                        item.find('strong') or \
                        link

            title = title_elem.get_text(strip=True) if title_elem else "제목 없음"

            # Try to find author
            author_elem = item.find(class_=re.compile(r'author|writer|name'))
            author = author_elem.get_text(strip=True) if author_elem else "작가 미상"

            # Try to find description
            desc_elem = item.find(class_=re.compile(r'desc|summary|intro'))
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            # For detailed information, we need to crawl the detail page
            # But for initial quick crawl, we'll collect basic info
            return {
                'title': title,
                'author': author,
                'description': description if description else f"{title} - 네이버 시리즈 웹소설",
                'platform': self.platform,
                'url': detail_url,
                'product_no': product_no,
                'keywords': []  # Will be enriched from detail page
            }

        except Exception as e:
            logger.warning(f"Error parsing list item: {e}")
            return None

    def crawl_detail_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Crawl detail page for complete information

        Args:
            url: Detail page URL

        Returns:
            Complete novel data
        """
        soup = self.fetch_page(url)

        if not soup:
            return None

        try:
            # Extract detailed information
            title_elem = soup.find('h2', class_=re.compile(r'title|subject')) or \
                        soup.find(class_='end_title')
            title = title_elem.get_text(strip=True) if title_elem else "제목 없음"

            # Author
            author_elem = soup.find(class_=re.compile(r'author|writer')) or \
                         soup.find('span', class_='writer')
            author = author_elem.get_text(strip=True) if author_elem else "작가 미상"

            # Description/Synopsis
            desc_elem = soup.find(class_=re.compile(r'summary|synopsis|intro|description')) or \
                       soup.find('div', class_='section_synopsis')
            description = desc_elem.get_text(strip=True) if desc_elem else f"{title} - 네이버 시리즈 웹소설"

            # Keywords/Tags/Genre
            keywords = []
            tag_container = soup.find(class_=re.compile(r'tag|genre|category'))

            if tag_container:
                tag_elems = tag_container.find_all(['a', 'span'], class_=re.compile(r'tag|genre'))
                keywords = [tag.get_text(strip=True) for tag in tag_elems if tag.get_text(strip=True)]

            # If no tags found, try to extract from metadata or breadcrumb
            if not keywords:
                genre_elem = soup.find(class_='genre') or soup.find(text=re.compile(r'장르'))
                if genre_elem:
                    keywords.append(genre_elem.get_text(strip=True))

            return {
                'title': title,
                'author': author,
                'description': description,
                'platform': self.platform,
                'url': url,
                'keywords': keywords or ['웹소설', '네이버시리즈']
            }

        except Exception as e:
            logger.error(f"Error parsing detail page {url}: {e}")
            return None

    def crawl_with_details(self, max_pages: Optional[int] = None,
                          fetch_details: bool = False) -> List[Dict[str, Any]]:
        """
        Crawl with option to fetch detail pages

        Args:
            max_pages: Maximum pages to crawl
            fetch_details: Whether to fetch each detail page

        Returns:
            List of novel data
        """
        # First, get all novels from list pages
        novels = self.crawl_all(max_pages)

        if not fetch_details:
            return novels

        # Enrich with detail page data
        logger.info(f"Fetching details for {len(novels)} novels...")
        enriched_novels = []

        for i, novel in enumerate(novels, 1):
            logger.info(f"Fetching detail {i}/{len(novels)}: {novel['title']}")

            detail_data = self.crawl_detail_page(novel['url'])

            if detail_data:
                enriched_novels.append(detail_data)
            else:
                # Keep original data if detail fetch fails
                enriched_novels.append(novel)

        return enriched_novels
