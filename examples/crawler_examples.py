#!/usr/bin/env python3
"""
Crawler Usage Examples

다양한 크롤링 시나리오 예시 모음
"""

import asyncio
import sys

sys.path.insert(0, "/home/user/korea_webnovel_recommender")

from backend.app.services.crawler.skyvern_client import SkyvernClient
from backend.app.services.crawler.platforms.naver import NaverSeriesCrawler
from backend.app.services.crawler.platforms.kakao import KakaoPageCrawler
from backend.app.services.crawler.platforms.ridi import RidibooksCrawler
from backend.app.services.crawler.utils import (
    save_crawled_novels,
    filter_novels_by_keywords,
    merge_novel_lists,
    get_crawl_statistics
)


async def example_1_basic_crawl():
    """예시 1: 기본 크롤링 - 네이버 시리즈에서 판타지 소설 수집"""
    print("\n=== 예시 1: 기본 크롤링 ===")

    client = SkyvernClient()
    crawler = NaverSeriesCrawler(client)

    novels = await crawler.crawl_genre(
        genre="판타지",
        limit=10
    )

    print(f"수집된 소설: {len(novels)}개")
    for i, novel in enumerate(novels[:3], 1):
        print(f"{i}. {novel['title']} - {novel['author']}")


async def example_2_multiple_genres():
    """예시 2: 여러 장르 동시 수집"""
    print("\n=== 예시 2: 여러 장르 수집 ===")

    client = SkyvernClient()
    crawler = KakaoPageCrawler(client)

    genres = ["판타지", "로맨스", "무협"]
    novels = await crawler.crawl_multiple_genres(
        genres=genres,
        limit_per_genre=10
    )

    stats = get_crawl_statistics(novels)
    print(f"총 {stats['total']}개 소설 수집")
    print(f"장르별: {stats['keywords']}")


async def example_3_special_content():
    """예시 3: 특수 콘텐츠 수집 (랭킹, 베스트셀러 등)"""
    print("\n=== 예시 3: 랭킹 수집 ===")

    client = SkyvernClient()
    kakao = KakaoPageCrawler(client)

    # 실시간 랭킹
    ranking = await kakao.crawl_ranking(ranking_type="realtime", limit=10)
    print(f"실시간 랭킹 {len(ranking)}개 수집")

    # 완결 작품
    completed = await kakao.crawl_completed_novels(limit=10)
    print(f"완결 작품 {len(completed)}개 수집")


async def example_4_multiple_platforms():
    """예시 4: 여러 플랫폼에서 동시 수집"""
    print("\n=== 예시 4: 멀티 플랫폼 크롤링 ===")

    client = SkyvernClient()

    # 3개 플랫폼 동시 실행
    tasks = [
        NaverSeriesCrawler(client).crawl_genre("판타지", 5),
        KakaoPageCrawler(client).crawl_genre("판타지", 5),
        RidibooksCrawler(client).crawl_genre("판타지", 5),
    ]

    results = await asyncio.gather(*tasks)

    # 결과 병합
    all_novels = merge_novel_lists(*results)
    print(f"총 {len(all_novels)}개 고유 소설 수집")


async def example_5_with_filtering():
    """예시 5: 키워드 필터링과 함께 수집"""
    print("\n=== 예시 5: 필터링 크롤링 ===")

    client = SkyvernClient()
    crawler = NaverSeriesCrawler(client)

    # 소설 수집
    novels = await crawler.crawl_genre("판타지", limit=20)

    # 키워드 필터링
    filtered = filter_novels_by_keywords(
        novels,
        required_keywords=["회귀", "성장"],
        excluded_keywords=["19금"]
    )

    print(f"전체: {len(novels)}개 → 필터링 후: {len(filtered)}개")


async def example_6_save_to_database():
    """예시 6: 데이터베이스 저장"""
    print("\n=== 예시 6: DB 저장 ===")

    client = SkyvernClient()
    crawler = RidibooksCrawler(client)

    # 베스트셀러 수집
    novels = await crawler.crawl_bestsellers(limit=10)

    # 데이터베이스 저장
    saved_count = await save_crawled_novels(novels)
    print(f"{saved_count}개 소설이 데이터베이스에 저장되었습니다")


async def example_7_with_login():
    """예시 7: 로그인이 필요한 성인 콘텐츠 수집"""
    print("\n=== 예시 7: 성인 콘텐츠 (로그인) ===")

    client = SkyvernClient()
    crawler = NaverSeriesCrawler(client)

    # 로그인 (환경변수에서 자동으로 읽어옴)
    # NAVER_USERNAME, NAVER_PASSWORD가 설정되어 있어야 함

    novels = await crawler.crawl_genre(
        genre="BL",
        limit=10,
        include_adult=True  # 성인 콘텐츠 포함
    )

    print(f"{len(novels)}개 소설 수집 (성인 콘텐츠 포함)")


async def main():
    """모든 예시 실행"""
    print("=" * 60)
    print("Skyvern 크롤러 사용 예시")
    print("=" * 60)

    try:
        # 실행할 예시 선택 (주석 해제)
        await example_1_basic_crawl()
        # await example_2_multiple_genres()
        # await example_3_special_content()
        # await example_4_multiple_platforms()
        # await example_5_with_filtering()
        # await example_6_save_to_database()
        # await example_7_with_login()

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        print("\n설정 확인:")
        print("1. Ollama 실행 여부: ollama serve")
        print("2. 모델 다운로드: ollama pull qwen2.5:7b-instruct")
        print("3. Skyvern 설치: pip install skyvern playwright")
        print("4. .env 설정: ENABLE_SKYVERN=true")


if __name__ == "__main__":
    asyncio.run(main())
