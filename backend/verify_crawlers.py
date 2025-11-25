import asyncio
import inspect
from backend.app.services.crawler.platforms.naver import NaverSeriesCrawlerEnhanced
from backend.app.services.crawler.platforms.kakao import KakaoPageCrawler
from backend.app.services.crawler.platforms.ridi import RidibooksCrawler

class MockSkyvernClient:
    def __init__(self):
        pass

async def verify_crawlers():
    print("Verifying Crawlers...")
    client = MockSkyvernClient()

    # 1. Verify Naver Crawler
    print("\n[Naver Crawler]")
    naver = NaverSeriesCrawlerEnhanced(client)
    
    # Check methods
    assert hasattr(naver, 'crawl_all_novels')
    assert hasattr(naver, 'crawl_new_releases')
    
    # Check prompt content (static check by reading file)
    with open('backend/app/services/crawler/platforms/naver.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if "목록 페이지의 소개글은 잘려있습니다" in content:
            print("✅ Naver prompt updated correctly (Truncated description warning)")
        else:
            print("❌ Naver prompt missing truncated description warning")
            
        if "상세 페이지의 전체 소개글 (필수)" in content:
            print("✅ Naver prompt updated correctly (Mandatory detail page)")
        else:
            print("❌ Naver prompt missing mandatory detail page instruction")

    # 2. Verify Kakao Crawler
    print("\n[Kakao Crawler]")
    kakao = KakaoPageCrawler(client)
    
    # Check methods
    assert hasattr(kakao, 'crawl_all_novels')
    assert hasattr(kakao, 'crawl_new_releases')
    
    # Check prompt content
    with open('backend/app/services/crawler/platforms/kakao.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if "목록 페이지에는 제목과 이미지만 있습니다" in content:
            print("✅ Kakao prompt updated correctly (Title/Image only warning)")
        else:
            print("❌ Kakao prompt missing title/image only warning")
            
        if "무한 스크롤이 적용되어 있습니다" in content:
            print("✅ Kakao prompt updated correctly (Infinite scroll instruction)")
        else:
            print("❌ Kakao prompt missing infinite scroll instruction")

    # 3. Verify Ridi Crawler
    print("\n[Ridi Crawler]")
    ridi = RidibooksCrawler(client)
    
    # Check methods
    assert hasattr(ridi, 'crawl_all_novels')
    assert hasattr(ridi, 'crawl_new_releases')
    
    # Check crawl_new_releases signature
    sig = inspect.signature(ridi.crawl_new_releases)
    if 'genre' in sig.parameters:
        print("✅ Ridi crawl_new_releases has 'genre' parameter")
    else:
        print("❌ Ridi crawl_new_releases MISSING 'genre' parameter")

    # Check prompt content
    with open('backend/app/services/crawler/platforms/ridi.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if "신작 카테고리 탐색" in content:
            print("✅ Ridi prompt updated correctly (New releases navigation)")
        else:
            print("❌ Ridi prompt missing new releases navigation instruction")
            
        if "category/new-releases/" in content:
            print("✅ Ridi URL structure looks correct")
        else:
            print("❌ Ridi URL structure might be incorrect")

if __name__ == "__main__":
    asyncio.run(verify_crawlers())
