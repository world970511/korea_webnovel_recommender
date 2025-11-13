"""
Main Crawler Script
Crawl web novels from Naver Series and save to database
"""
import json
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crawlers.naver_crawler import NaverSeriesCrawler
from processors.data_processor import DataProcessor
from app.services.vector_db import vector_db_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'crawler_{datetime.now():%Y%m%d_%H%M%S}.log')
    ]
)

logger = logging.getLogger(__name__)


def save_to_json(novels: list, filename: str):
    """Save novels to JSON file"""
    output_path = Path(__file__).parent.parent.parent / "data" / filename

    # Create data directory if not exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(novels, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(novels)} novels to {output_path}")
    return output_path


def crawl_naver_series(max_pages: int = None,
                      fetch_details: bool = False,
                      save_json: bool = True,
                      save_db: bool = True) -> list:
    """
    Crawl Naver Series

    Args:
        max_pages: Maximum pages to crawl (None = all)
        fetch_details: Fetch detail pages for complete info
        save_json: Save to JSON file
        save_db: Save to database

    Returns:
        List of processed novels
    """
    logger.info("=" * 80)
    logger.info("Starting Naver Series Crawler")
    logger.info("=" * 80)

    # Initialize crawler
    crawler = NaverSeriesCrawler(delay=1.5)

    try:
        # Crawl novels
        if fetch_details:
            logger.info("Crawling with detail pages (slower but more complete)")
            raw_novels = crawler.crawl_with_details(max_pages=max_pages, fetch_details=True)
        else:
            logger.info("Crawling list pages only (faster but basic info)")
            raw_novels = crawler.crawl_all(max_pages=max_pages)

        logger.info(f"Crawled {len(raw_novels)} novels")

        # Process data
        logger.info("Processing and validating data...")
        processed_novels = DataProcessor.process_batch(raw_novels, remove_duplicates=True)

        logger.info(f"Processed {len(processed_novels)} valid novels")

        # Save to JSON
        if save_json:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = f"naver_novels_{timestamp}.json"
            save_to_json(processed_novels, json_file)

        # Save to database
        if save_db and processed_novels:
            logger.info("Saving to database...")
            try:
                vector_db_service.add_novels(processed_novels)
                count = vector_db_service.count_novels()
                logger.info(f"✅ Database updated! Total novels in DB: {count}")
            except Exception as e:
                logger.error(f"Failed to save to database: {e}")
                logger.info("Data saved to JSON file only")

        logger.info("=" * 80)
        logger.info(f"✨ Crawling complete! Collected {len(processed_novels)} novels")
        logger.info("=" * 80)

        return processed_novels

    except Exception as e:
        logger.error(f"Crawling failed: {e}", exc_info=True)
        return []

    finally:
        crawler.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Crawl Korean web novels')

    parser.add_argument(
        '--platform',
        type=str,
        default='naver',
        choices=['naver', 'kakao', 'munpia'],
        help='Platform to crawl (default: naver)'
    )

    parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        help='Maximum number of pages to crawl (default: all pages)'
    )

    parser.add_argument(
        '--details',
        action='store_true',
        help='Fetch detail pages for complete information (slower)'
    )

    parser.add_argument(
        '--no-json',
        action='store_true',
        help='Do not save to JSON file'
    )

    parser.add_argument(
        '--no-db',
        action='store_true',
        help='Do not save to database'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: crawl only 2 pages'
    )

    args = parser.parse_args()

    # Test mode
    if args.test:
        logger.info("🧪 Running in TEST mode (2 pages only)")
        args.max_pages = 2

    # Only Naver is implemented for now
    if args.platform != 'naver':
        logger.error(f"Platform '{args.platform}' not yet implemented. Only 'naver' is available.")
        sys.exit(1)

    # Run crawler
    novels = crawl_naver_series(
        max_pages=args.max_pages,
        fetch_details=args.details,
        save_json=not args.no_json,
        save_db=not args.no_db
    )

    if novels:
        logger.info(f"✅ Success! Collected {len(novels)} novels")
        sys.exit(0)
    else:
        logger.error("❌ No novels collected")
        sys.exit(1)


if __name__ == "__main__":
    main()
