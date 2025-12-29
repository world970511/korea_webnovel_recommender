"""
Crawler Service for Web Novel Platforms

This module provides web scraping capabilities using traditional CSS selectors
for multiple Korean web novel platforms with different UI patterns.
"""

from .traditional_crawler_client import TraditionalCrawlerClient
from .base import BaseCrawler

# Backward compatibility
CrawlerClient = TraditionalCrawlerClient

__all__ = ["TraditionalCrawlerClient", "CrawlerClient", "BaseCrawler"]
