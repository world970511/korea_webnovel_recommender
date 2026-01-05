"""
Crawler Service for Web Novel Platforms

This module provides web scraping capabilities using traditional CSS selectors
for multiple Korean web novel platforms with different UI patterns.
"""

from .crawler_client import CrawlerClient
from .base import BaseCrawler

# Backward compatibility
CrawlerClient = CrawlerClient

__all__ = ["CrawlerClient", "BaseCrawler"]
