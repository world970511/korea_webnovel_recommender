
import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from backend.app.services.crawler.platforms.kakao import KakaoPageCrawler
from backend.app.services.crawler.crawler_client import CrawlerClient

async def test_kakao_crawler():
    logger.info("Starting Kakao Crawler Test...")
    
    # 1. Initialize Client
    client = CrawlerClient(headless=False) # Run visible to see what happens
    
    # 2. Check if create_page exists (pre-check)
    if not hasattr(client, 'create_page'):
        logger.error("CRITICAL: CrawlerClient is missing 'create_page' method!")
    
    # 3. Initialize Crawler
    crawler = KakaoPageCrawler(client)
    
    try:
        # 4. Test crawl_new_releases (smaller scope)
        logger.info("Testing crawl_new_releases...")
        novels = await crawler.crawl_new_releases(limit=50)
        
        logger.info(f"Successfully crawled {len(novels)} novels")
        for novel in novels:
            print(f"- [{novel['title']}] {novel['url']}")
            
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
    finally:
        # Cleanup if client has close method
        if hasattr(client, 'close'):
            await client.close()
        elif client.browser:
            await client.browser.close()
        if client.playwright:
            await client.playwright.stop()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(test_kakao_crawler())
