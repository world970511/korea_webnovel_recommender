"""
Base Crawler Class
"""
import time
import logging
import requests
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """Base class for all web novel crawlers"""

    def __init__(self, platform: str, base_url: str, delay: float = 1.5):
        """
        Initialize base crawler

        Args:
            platform: Platform name (e.g., "네이버시리즈")
            base_url: Base URL of the platform
            delay: Delay between requests in seconds (default: 1.5s)
        """
        self.platform = platform
        self.base_url = base_url
        self.delay = delay

        # Setup session with headers to mimic browser
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })

        logger.info(f"Initialized {platform} crawler")

    def fetch_page(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Fetch a page with retries

        Args:
            url: URL to fetch
            max_retries: Maximum number of retries

        Returns:
            BeautifulSoup object or None if failed
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching: {url} (attempt {attempt + 1}/{max_retries})")

                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                # Respect rate limiting
                time.sleep(self.delay)

                return BeautifulSoup(response.text, 'lxml')

            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to fetch {url}: {e}")

                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None

    @abstractmethod
    def crawl_list_page(self, page: int = 1) -> List[Dict[str, Any]]:
        """
        Crawl a list page and extract novel metadata

        Args:
            page: Page number

        Returns:
            List of novel metadata dictionaries
        """
        pass

    @abstractmethod
    def crawl_detail_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Crawl a detail page to get full novel information

        Args:
            url: Detail page URL

        Returns:
            Novel data dictionary or None
        """
        pass

    @abstractmethod
    def get_total_pages(self) -> int:
        """
        Get total number of pages to crawl

        Returns:
            Total page count
        """
        pass

    def crawl_all(self, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Crawl all pages and collect novels

        Args:
            max_pages: Maximum number of pages to crawl (None = all)

        Returns:
            List of all novel data
        """
        logger.info(f"Starting crawl for {self.platform}")

        total_pages = self.get_total_pages()
        pages_to_crawl = min(total_pages, max_pages) if max_pages else total_pages

        logger.info(f"Total pages to crawl: {pages_to_crawl}")

        all_novels = []

        for page in range(1, pages_to_crawl + 1):
            logger.info(f"Crawling page {page}/{pages_to_crawl}")

            try:
                novels = self.crawl_list_page(page)
                all_novels.extend(novels)
                logger.info(f"Found {len(novels)} novels on page {page}")

            except Exception as e:
                logger.error(f"Error crawling page {page}: {e}")
                continue

        logger.info(f"Crawl complete! Total novels collected: {len(all_novels)}")
        return all_novels

    def close(self):
        """Close the session"""
        self.session.close()
        logger.info(f"Closed {self.platform} crawler")
