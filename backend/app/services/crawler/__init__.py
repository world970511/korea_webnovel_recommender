"""
Crawler Service for Web Novel Platforms

This module provides web scraping capabilities using Skyvern + Ollama
for multiple Korean web novel platforms with different UI patterns.
"""

from backend.app.services.crawler.skyvern_client import SkyvernClient
from backend.app.services.crawler.base import BaseCrawler

__all__ = ["SkyvernClient", "BaseCrawler"]
