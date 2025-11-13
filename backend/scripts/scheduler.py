"""
Automated Crawler Scheduler
Run crawlers automatically on a schedule
"""
import logging
import sys
from pathlib import Path
from datetime import datetime, time
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main_crawler import crawl_naver_series

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'scheduler_{datetime.now():%Y%m%d}.log')
    ]
)

logger = logging.getLogger(__name__)


def scheduled_crawl():
    """Run scheduled crawl task"""
    logger.info("=" * 80)
    logger.info(f"Starting scheduled crawl at {datetime.now()}")
    logger.info("=" * 80)

    try:
        # Crawl with details for complete information
        novels = crawl_naver_series(
            max_pages=None,  # Crawl all pages
            fetch_details=False,  # Quick crawl (list pages only)
            save_json=True,
            save_db=True
        )

        logger.info(f"✅ Scheduled crawl completed successfully! Collected {len(novels)} novels")

    except Exception as e:
        logger.error(f"❌ Scheduled crawl failed: {e}", exc_info=True)


def main():
    """Main scheduler entry point"""
    scheduler = BlockingScheduler()

    # Schedule daily crawl at midnight KST (15:00 UTC)
    # Adjust the hour based on your timezone
    trigger = CronTrigger(
        hour=0,      # Midnight
        minute=0,
        timezone='Asia/Seoul'
    )

    scheduler.add_job(
        scheduled_crawl,
        trigger=trigger,
        id='daily_crawl',
        name='Daily Web Novel Crawl',
        replace_existing=True
    )

    logger.info("=" * 80)
    logger.info("웹소설 크롤러 스케줄러 시작")
    logger.info("=" * 80)
    logger.info("스케줄: 매일 자정 (KST)")
    logger.info("다음 실행 시간: " + str(scheduler.get_jobs()[0].next_run_time))
    logger.info("=" * 80)
    logger.info("Press Ctrl+C to exit")
    logger.info("=" * 80)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
