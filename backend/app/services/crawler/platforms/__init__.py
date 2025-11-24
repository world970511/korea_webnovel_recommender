"""
Platform-specific crawlers

Each module implements a crawler for a specific web novel platform
with its unique UI patterns and navigation requirements.
"""

from backend.app.services.crawler.platforms.naver import NaverSeriesCrawler
from backend.app.services.crawler.platforms.kakao import KakaoPageCrawler
from backend.app.services.crawler.platforms.ridi import RidibooksCrawler

__all__ = ["NaverSeriesCrawler", "KakaoPageCrawler", "RidibooksCrawler"]
