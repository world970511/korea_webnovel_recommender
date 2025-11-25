#!/usr/bin/env python3
"""
Novel Crawler CLI

Command-line interface for crawling web novels from various platforms
using Skyvern + Ollama integration.

Usage:
    python backend/crawl_novels.py --platform naver --genre 판타지 --limit 20
    python backend/crawl_novels.py --all --genres 판타지,로맨스 --limit 50
    python backend/crawl_novels.py --platform kakao --ranking realtime
"""

import asyncio
import argparse
import logging
import sys
from typing import List, Dict

# Add backend to path
sys.path.insert(0, "/home/user/korea_webnovel_recommender")

from backend.app.config import settings
from backend.app.services.crawler.skyvern_client import SkyvernClient
from backend.app.services.crawler.platforms.naver import NaverSeriesCrawler
from backend.app.services.crawler.platforms.kakao import KakaoPageCrawler
from backend.app.services.crawler.platforms.ridi import RidibooksCrawler
from backend.app.services.crawler.utils import (
    save_crawled_novels,
    deduplicate_novels,
    get_crawl_statistics,
    clean_novel_data,
)

# Configure logging
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
    Crawl novels from a specific platform.

    Args:
        platform: Platform name ("naver", "kakao", "ridi")
        genres: List of genres to crawl
        limit: Number of novels per genre
        include_adult: Whether to include adult content
        save_to_db: Whether to save to database

    Returns:
        List of crawled novels
    """
    logger.info(f"Starting crawl: platform={platform}, genres={genres}, limit={limit}")

    # Initialize Skyvern client
    client = SkyvernClient()

    if not client.is_available():
        logger.error("Skyvern is not available. Check configuration.")
        logger.info("Make sure to:")
        logger.info("1. Install Skyvern: pip install skyvern")
        logger.info("2. Install Ollama and run: ollama pull qwen2.5:7b-instruct")
        logger.info("3. Enable in .env: ENABLE_SKYVERN=true")
        return []

    # Select crawler
    crawlers = {
        "naver": NaverSeriesCrawler(client),
        "kakao": KakaoPageCrawler(client),
        "ridi": RidibooksCrawler(client),
    }

    crawler = crawlers.get(platform.lower())
    if not crawler:
        logger.error(f"Unknown platform: {platform}")
        logger.info(f"Available platforms: {', '.join(crawlers.keys())}")
        return []

    # Crawl logic
    if not genres:
        # If no genres specified, crawl all/default
        if platform == "ridi":
            # Ridi requires genre, so crawl all defined genres
            genres = list(crawler.GENRE_MAP.keys())
            logger.info(f"No genre specified for Ridi. Crawling all genres: {genres}")
        elif hasattr(crawler, "crawl_all_novels"):
            # Naver/Kakao support crawling all novels without genre
            try:
                logger.info(f"Crawling all novels from {platform}...")
                novels = await crawler.crawl_all_novels(
                    limit=limit,
                    include_adult=include_adult
                )
                
                # Clean and deduplicate
                novels = clean_novel_data(novels)
                novels = deduplicate_novels(novels)
                
                logger.info(f"Total unique novels collected: {len(novels)}")

                if save_to_db and novels:
                    saved_count = await save_crawled_novels(novels)
                    logger.info(f"Saved {saved_count} novels to database")
                
                return novels
            except Exception as e:
                logger.error(f"Failed to crawl all novels: {str(e)}")
                return []

    # Crawl specific genres (or all genres for Ridi)
    all_novels = []
    for genre in genres:
        try:
            logger.info(f"Crawling {genre} from {platform}...")
            
            # Ridi uses crawl_all_novels with genre arg, others might use crawl_genre
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
                logger.warning(f"Genre crawling not supported for {platform}. Using crawl_all_novels fallback.")
                novels = await crawler.crawl_all_novels(limit=limit, include_adult=include_adult)

            all_novels.extend(novels)
            logger.info(f"Collected {len(novels)} novels from {genre}")

            # Small delay between genres
            await asyncio.sleep(settings.crawler_delay_seconds)

        except Exception as e:
            logger.error(f"Failed to crawl {genre}: {str(e)}")
            continue

    # Clean and deduplicate
    all_novels = clean_novel_data(all_novels)
    all_novels = deduplicate_novels(all_novels)

    logger.info(f"Total unique novels collected: {len(all_novels)}")

    # Save to database
    if save_to_db and all_novels:
        saved_count = await save_crawled_novels(all_novels)
        logger.info(f"Saved {saved_count} novels to database")

    # Print statistics
    stats = get_crawl_statistics(all_novels)
    logger.info(f"Crawl statistics: {stats}")

    return all_novels


async def crawl_all_platforms(
    genres: List[str],
    limit: int,
    include_adult: bool = False,
    save_to_db: bool = True
) -> List[Dict]:
    """
    Crawl novels from all platforms.

    Args:
        genres: List of genres to crawl
        limit: Number of novels per genre per platform
        include_adult: Whether to include adult content
        save_to_db: Whether to save to database

    Returns:
        Combined list of crawled novels
    """
    platforms = ["naver", "kakao", "ridi"]
    all_novels = []

    for platform in platforms:
        try:
            novels = await crawl_platform(
                platform=platform,
                genres=genres,
                limit=limit,
                include_adult=include_adult,
                save_to_db=False  # Save all together at the end
            )
            all_novels.extend(novels)
        except Exception as e:
            logger.error(f"Failed to crawl {platform}: {str(e)}")
            continue

    # Deduplicate across platforms
    all_novels = deduplicate_novels(all_novels)

    # Save to database
    if save_to_db and all_novels:
        saved_count = await save_crawled_novels(all_novels)
        logger.info(f"Saved {saved_count} total novels to database")

    return all_novels


async def crawl_special(
    platform: str,
    mode: str,
    limit: int,
    save_to_db: bool = True
) -> List[Dict]:
    """
    Crawl special content (rankings, bestsellers, etc.)

    Args:
        platform: Platform name
        mode: Special mode (ranking, bestseller, new, completed)
        limit: Number of novels to collect
        save_to_db: Whether to save to database

    Returns:
        List of crawled novels
    """
    client = SkyvernClient()

    if not client.is_available():
        logger.error("Skyvern is not available")
        return []

    crawlers = {
        "naver": NaverSeriesCrawler(client),
        "kakao": KakaoPageCrawler(client),
        "ridi": RidibooksCrawler(client),
    }

    crawler = crawlers.get(platform.lower())
    if not crawler:
        logger.error(f"Unknown platform: {platform}")
        return []

    novels = []

    try:
        if mode == "ranking" and hasattr(crawler, "crawl_ranking"):
            novels = await crawler.crawl_ranking(limit=limit)
        elif mode == "bestseller" and hasattr(crawler, "crawl_bestsellers"):
            novels = await crawler.crawl_bestsellers(limit=limit)
        elif mode == "new" and hasattr(crawler, "crawl_new_releases"):
            novels = await crawler.crawl_new_releases(limit=limit)
        elif mode == "completed" and hasattr(crawler, "crawl_completed_novels"):
            novels = await crawler.crawl_completed_novels(limit=limit)
        elif mode == "top" and hasattr(crawler, "crawl_top_novels"):
            novels = await crawler.crawl_top_novels(limit=limit)
        else:
            logger.error(f"Mode '{mode}' not supported for {platform}")
            return []

        novels = clean_novel_data(novels)

        if save_to_db and novels:
            saved_count = await save_crawled_novels(novels)
            logger.info(f"Saved {saved_count} novels to database")

        return novels

    except Exception as e:
        logger.error(f"Failed to crawl {mode}: {str(e)}")
        return []


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Crawl web novels using Skyvern + Ollama"
    )

    parser.add_argument(
        "--platform",
        choices=["naver", "kakao", "ridi", "all"],
        help="Platform to crawl"
    )

    parser.add_argument(
        "--genres",
        type=str,
        help="Comma-separated list of genres (e.g., '판타지,로맨스,무협')"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of novels per genre (default: 20)"
    )

    parser.add_argument(
        "--adult",
        action="store_true",
        help="Include adult content (requires login credentials)"
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save to database (just print results)"
    )

    parser.add_argument(
        "--special",
        choices=["ranking", "bestseller", "new", "completed", "top"],
        help="Crawl special content instead of genres"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.platform:
        parser.error("--platform is required")

    if not args.special and not args.genres:
        # If no genres/special specified, default to empty list (implies "all" for supported platforms)
        pass

    # Parse genres
    genres = []
    if args.genres:
        genres = [g.strip() for g in args.genres.split(",")]

    # Check if Skyvern is enabled
    if not settings.enable_skyvern:
        logger.error("Skyvern is disabled in configuration")
        logger.info("Enable it in .env: ENABLE_SKYVERN=true")
        sys.exit(1)

    # Run crawler
    try:
        if args.special:
            # Special mode
            novels = asyncio.run(crawl_special(
                platform=args.platform,
                mode=args.special,
                limit=args.limit,
                save_to_db=not args.no_save
            ))
        elif args.platform == "all":
            # Crawl all platforms
            novels = asyncio.run(crawl_all_platforms(
                genres=genres,
                limit=args.limit,
                include_adult=args.adult,
                save_to_db=not args.no_save
            ))
        else:
            # Crawl single platform
            novels = asyncio.run(crawl_platform(
                platform=args.platform,
                genres=genres,
                limit=args.limit,
                include_adult=args.adult,
                save_to_db=not args.no_save
            ))

        logger.info(f"\nCrawling complete! Collected {len(novels)} novels.")

        if not args.no_save:
            logger.info("Novels have been saved to the database.")

    except KeyboardInterrupt:
        logger.info("\nCrawling interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Crawling failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
