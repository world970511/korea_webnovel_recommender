"""
Platform-specific crawlers

Each module implements a crawler for a specific web novel platform
with its unique UI patterns and navigation requirements.
"""

from .naver import NaverSeriesCrawler
from .kakao import KakaoPageCrawler
from .ridi import RidibooksCrawler

__all__ = ["NaverSeriesCrawler", "KakaoPageCrawler", "RidibooksCrawler"]
