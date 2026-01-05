#!/usr/bin/env python3
"""
웹소설 크롤러 CLI

다양한 플랫폼(네이버, 카카오, 리디)에서 웹소설을 크롤링하는 커맨드라인 인터페이스.
Playwright를 사용하여 웹 페이지를 렌더링하고 데이터를 수집합니다.

사용 예시:
    # 카카오 신작 5개 수집
    python backend/crawl_novels.py --platform kakao --special new --limit 5

    # 네이버 판타지 장르 20개 수집
    python backend/crawl_novels.py --platform naver --genres 판타지 --limit 20

    # 리디북스 로맨스, 판타지 각 10개씩 수집
    python backend/crawl_novels.py --platform ridi --genres 로맨스,판타지 --limit 10

    # 모든 플랫폼에서 수집
    python backend/crawl_novels.py --platform all --limit 20
"""

import asyncio
import argparse
import logging
import sys
from typing import List, Dict

# 백엔드 경로를 Python 경로에 추가 (import를 위해)
sys.path.insert(0, "/home/user/korea_webnovel_recommender")

from app.config import settings
from app.services.crawler.traditional_crawler_client import TraditionalCrawlerClient
from app.services.crawler.platforms.naver import NaverSeriesCrawler
from app.services.crawler.platforms.kakao import KakaoPageCrawler
from app.services.crawler.platforms.ridi import RidibooksCrawler
from app.services.crawler.utils import (
    save_crawled_novels,      # DB에 소설 저장
    deduplicate_novels,       # 중복 소설 제거
    get_crawl_statistics,     # 크롤링 통계 생성
    clean_novel_data,         # 소설 데이터 정리
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def crawl_platform(
    platform: str,
    genres: List[str],
    limit: int,
    include_adult: bool = False,
    save_to_db: bool = True
) -> List[Dict]:
    """
    특정 플랫폼에서 웹소설을 크롤링합니다.

    Args:
        platform: 플랫폼 이름 ("naver", "kakao", "ridi")
        genres: 크롤링할 장르 리스트 (예: ["판타지", "로맨스"])
        limit: 장르당 수집할 소설 수
        include_adult: 성인 콘텐츠 포함 여부
        save_to_db: 데이터베이스 저장 여부

    Returns:
        크롤링된 소설 리스트 (각 소설은 Dict 형태)
    """
    logger.info(f"크롤링 시작: platform={platform}, genres={genres}, limit={limit}")

    # Playwright 기반 크롤러 클라이언트 초기화
    client = TraditionalCrawlerClient()

    # 크롤러 클라이언트 사용 가능 여부 확인
    if not client.is_available():
        logger.error("Playwright를 사용할 수 없습니다. 설정을 확인하세요.")
        logger.info("설치 방법:")
        logger.info("1. Playwright 설치: pip install playwright")
        logger.info("2. 브라우저 설치: python -m playwright install chromium")
        return []

    # 플랫폼별 크롤러 매핑
    crawlers = {
        "naver": NaverSeriesCrawler(client),
        "kakao": KakaoPageCrawler(client),
        "ridi": RidibooksCrawler(client),
    }

    # 요청한 플랫폼의 크롤러 가져오기
    crawler = crawlers.get(platform.lower())
    if not crawler:
        logger.error(f"알 수 없는 플랫폼: {platform}")
        logger.info(f"사용 가능한 플랫폼: {', '.join(crawlers.keys())}")
        return []

    # 크롤링 로직
    if not genres:
        # 장르가 지정되지 않은 경우
        if platform == "ridi":
            # 리디북스는 장르가 필수이므로 모든 장르 크롤링
            genres = list(crawler.GENRE_MAP.keys())
            logger.info(f"리디북스는 장르가 필수입니다. 모든 장르 크롤링: {genres}")
        elif hasattr(crawler, "crawl_all_novels"):
            # 네이버/카카오는 장르 없이 전체 크롤링 지원
            try:
                logger.info(f"{platform}에서 전체 소설 크롤링 중...")
                novels = await crawler.crawl_all_novels(
                    limit=limit,
                    include_adult=include_adult
                )

                # 데이터 정리 및 중복 제거
                novels = clean_novel_data(novels)
                novels = deduplicate_novels(novels)

                logger.info(f"총 {len(novels)}개의 고유 소설 수집 완료")

                # 데이터베이스 저장
                if save_to_db and novels:
                    saved_count = await save_crawled_novels(novels)
                    logger.info(f"{saved_count}개의 소설을 데이터베이스에 저장했습니다")

                return novels
            except Exception as e:
                logger.error(f"전체 소설 크롤링 실패: {str(e)}")
                return []

    # 특정 장르 크롤링 (또는 리디북스의 경우 모든 장르)
    all_novels = []
    for genre in genres:
        try:
            logger.info(f"{platform}에서 {genre} 장르 크롤링 중...")

            # 리디북스는 crawl_all_novels에 genre 인자 전달
            # 다른 플랫폼은 crawl_genre 메서드 사용
            if platform == "ridi":
                novels = await crawler.crawl_all_novels(
                    genre=genre,
                    limit=limit,
                    include_adult=include_adult
                )
            elif hasattr(crawler, "crawl_genre"):
                novels = await crawler.crawl_genre(
                    genre=genre,
                    limit=limit,
                    include_adult=include_adult
                )
            else:
                # crawl_genre 메서드가 없는 경우 crawl_all_novels 대체 사용
                logger.warning(f"{platform}은 장르별 크롤링을 지원하지 않습니다. crawl_all_novels를 대신 사용합니다.")
                novels = await crawler.crawl_all_novels(limit=limit, include_adult=include_adult)

            all_novels.extend(novels)
            logger.info(f"{genre}에서 {len(novels)}개의 소설 수집")

            # 장르 간 작은 딜레이 (서버 부하 방지)
            await asyncio.sleep(settings.crawler_delay_seconds)

        except Exception as e:
            logger.error(f"{genre} 크롤링 실패: {str(e)}")
            continue

    # 데이터 정리 및 중복 제거
    all_novels = clean_novel_data(all_novels)
    all_novels = deduplicate_novels(all_novels)

    logger.info(f"총 {len(all_novels)}개의 고유 소설 수집 완료")

    # 데이터베이스 저장
    if save_to_db and all_novels:
        saved_count = await save_crawled_novels(all_novels)
        logger.info(f"{saved_count}개의 소설을 데이터베이스에 저장했습니다")

    # 통계 출력
    stats = get_crawl_statistics(all_novels)
    logger.info(f"크롤링 통계: {stats}")

    return all_novels


async def crawl_all_platforms(
    genres: List[str],
    limit: int,
    include_adult: bool = False,
    save_to_db: bool = True
) -> List[Dict]:
    """
    모든 플랫폼에서 웹소설을 크롤링합니다.

    Args:
        genres: 크롤링할 장르 리스트
        limit: 플랫폼당 장르당 수집할 소설 수
        include_adult: 성인 콘텐츠 포함 여부
        save_to_db: 데이터베이스 저장 여부

    Returns:
        모든 플랫폼에서 수집한 소설 통합 리스트
    """
    platforms = ["naver", "kakao", "ridi"]
    all_novels = []

    # 각 플랫폼별로 순차 크롤링
    for platform in platforms:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"{platform.upper()} 플랫폼 크롤링 시작")
            logger.info(f"{'='*50}\n")

            novels = await crawl_platform(
                platform=platform,
                genres=genres,
                limit=limit,
                include_adult=include_adult,
                save_to_db=False  # 마지막에 한 번에 저장
            )
            all_novels.extend(novels)

            logger.info(f"{platform}에서 {len(novels)}개 수집 완료\n")
        except Exception as e:
            logger.error(f"{platform} 크롤링 실패: {str(e)}")
            continue

    # 플랫폼 간 중복 제거 (동일한 작품이 여러 플랫폼에 있을 수 있음)
    all_novels = deduplicate_novels(all_novels)
    logger.info(f"\n전체 플랫폼에서 총 {len(all_novels)}개의 고유 소설 수집")

    # 데이터베이스 저장
    if save_to_db and all_novels:
        saved_count = await save_crawled_novels(all_novels)
        logger.info(f"{saved_count}개의 소설을 데이터베이스에 저장했습니다")

    return all_novels


async def crawl_special(
    platform: str,
    mode: str,
    limit: int,
    save_to_db: bool = True
) -> List[Dict]:
    """
    특수 컨텐츠를 크롤링합니다 (랭킹, 베스트셀러, 신작 등).

    Args:
        platform: 플랫폼 이름
        mode: 특수 모드 (ranking, bestseller, new, completed, top)
        limit: 수집할 소설 수
        save_to_db: 데이터베이스 저장 여부

    Returns:
        크롤링된 소설 리스트
    """
    logger.info(f"{platform}에서 {mode} 모드로 크롤링 시작")

    # Playwright 기반 크롤러 클라이언트 초기화
    client = TraditionalCrawlerClient()

    if not client.is_available():
        logger.error("Playwright를 사용할 수 없습니다")
        return []

    # 플랫폼별 크롤러 매핑
    crawlers = {
        "naver": NaverSeriesCrawler(client),
        "kakao": KakaoPageCrawler(client),
        "ridi": RidibooksCrawler(client),
    }

    crawler = crawlers.get(platform.lower())
    if not crawler:
        logger.error(f"알 수 없는 플랫폼: {platform}")
        return []

    novels = []

    try:
        # 모드별 크롤링 메서드 호출
        if mode == "ranking" and hasattr(crawler, "crawl_ranking"):
            # 실시간 랭킹
            novels = await crawler.crawl_ranking(limit=limit)
        elif mode == "bestseller" and hasattr(crawler, "crawl_bestsellers"):
            # 베스트셀러
            novels = await crawler.crawl_bestsellers(limit=limit)
        elif mode == "new" and hasattr(crawler, "crawl_new_releases"):
            # 신작
            novels = await crawler.crawl_new_releases(limit=limit)
        elif mode == "completed" and hasattr(crawler, "crawl_completed_novels"):
            # 완결작
            novels = await crawler.crawl_completed_novels(limit=limit)
        elif mode == "top" and hasattr(crawler, "crawl_top_novels"):
            # 인기작
            novels = await crawler.crawl_top_novels(limit=limit)
        else:
            logger.error(f"'{mode}' 모드는 {platform}에서 지원하지 않습니다")
            return []

        # 데이터 정리
        novels = clean_novel_data(novels)
        logger.info(f"{len(novels)}개의 소설 수집 완료")

        # 데이터베이스 저장
        if save_to_db and novels:
            saved_count = await save_crawled_novels(novels)
            logger.info(f"{saved_count}개의 소설을 데이터베이스에 저장했습니다")

        return novels

    except Exception as e:
        logger.error(f"{mode} 크롤링 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def main():
    """CLI 메인 진입점."""
    parser = argparse.ArgumentParser(
        description="Playwright를 사용한 웹소설 크롤러",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 카카오 신작 5개 수집
  python crawl_novels.py --platform kakao --special new --limit 5

  # 네이버 판타지 20개 수집
  python crawl_novels.py --platform naver --genres 판타지 --limit 20

  # 리디북스 로맨스, 판타지 각 10개씩
  python crawl_novels.py --platform ridi --genres 로맨스,판타지 --limit 10

  # 모든 플랫폼에서 수집
  python crawl_novels.py --platform all --limit 20
        """
    )

    parser.add_argument(
        "--platform",
        choices=["naver", "kakao", "ridi", "all"],
        required=True,
        help="크롤링할 플랫폼 선택"
    )

    parser.add_argument(
        "--genres",
        type=str,
        help="쉼표로 구분된 장르 리스트 (예: '판타지,로맨스,무협')"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="장르당 수집할 소설 수 (기본값: 20)"
    )

    parser.add_argument(
        "--adult",
        action="store_true",
        help="성인 콘텐츠 포함 (로그인 정보 필요)"
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="데이터베이스에 저장하지 않음 (결과만 출력)"
    )

    parser.add_argument(
        "--special",
        choices=["ranking", "bestseller", "new", "completed", "top"],
        help="특수 컨텐츠 크롤링 (장르 대신 사용)"
    )

    args = parser.parse_args()

    # 장르 파싱
    genres = []
    if args.genres:
        genres = [g.strip() for g in args.genres.split(",")]

    # 크롤러 실행
    try:
        if args.special:
            # 특수 모드 (랭킹, 신작 등)
            logger.info(f"\n{'='*50}")
            logger.info(f"특수 모드: {args.special}")
            logger.info(f"{'='*50}\n")

            novels = asyncio.run(crawl_special(
                platform=args.platform,
                mode=args.special,
                limit=args.limit,
                save_to_db=not args.no_save
            ))
        elif args.platform == "all":
            # 모든 플랫폼 크롤링
            logger.info(f"\n{'='*50}")
            logger.info("모든 플랫폼 크롤링")
            logger.info(f"{'='*50}\n")

            novels = asyncio.run(crawl_all_platforms(
                genres=genres,
                limit=args.limit,
                include_adult=args.adult,
                save_to_db=not args.no_save
            ))
        else:
            # 단일 플랫폼 크롤링
            novels = asyncio.run(crawl_platform(
                platform=args.platform,
                genres=genres,
                limit=args.limit,
                include_adult=args.adult,
                save_to_db=not args.no_save
            ))

        # 최종 결과 출력
        logger.info(f"\n{'='*50}")
        logger.info(f"크롤링 완료! 총 {len(novels)}개의 소설 수집")
        logger.info(f"{'='*50}\n")

        if not args.no_save:
            logger.info("소설이 데이터베이스에 저장되었습니다.")
        else:
            logger.info("--no-save 옵션으로 데이터베이스에 저장하지 않았습니다.")

    except KeyboardInterrupt:
        logger.info("\n\n사용자에 의해 크롤링이 중단되었습니다")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n크롤링 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
