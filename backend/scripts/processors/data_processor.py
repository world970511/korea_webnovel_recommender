"""
Data Processor for cleaning and validating crawled data
"""
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and validate crawled novel data"""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean text by removing extra whitespace and special characters

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters that might cause issues
        text = text.strip()

        return text

    @staticmethod
    def validate_novel(novel: Dict[str, Any]) -> bool:
        """
        Validate novel data

        Args:
            novel: Novel dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['title', 'author', 'description', 'platform', 'url']

        # Check all required fields exist and are not empty
        for field in required_fields:
            if field not in novel or not novel[field]:
                logger.warning(f"Novel missing or empty field: {field}")
                return False

        # Check title length (should be reasonable)
        if len(novel['title']) < 2 or len(novel['title']) > 200:
            logger.warning(f"Invalid title length: {novel['title']}")
            return False

        # Check URL format
        if not novel['url'].startswith('http'):
            logger.warning(f"Invalid URL format: {novel['url']}")
            return False

        # Check description length
        if len(novel['description']) < 10:
            logger.warning(f"Description too short for: {novel['title']}")
            return False

        return True

    @staticmethod
    def process_novel(novel: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and clean a single novel

        Args:
            novel: Raw novel data

        Returns:
            Processed novel data
        """
        processed = {}

        # Clean text fields
        processed['title'] = DataProcessor.clean_text(novel.get('title', ''))
        processed['author'] = DataProcessor.clean_text(novel.get('author', ''))
        processed['description'] = DataProcessor.clean_text(novel.get('description', ''))
        processed['platform'] = novel.get('platform', '')
        processed['url'] = novel.get('url', '')

        # Process keywords
        keywords = novel.get('keywords', [])
        if isinstance(keywords, list):
            processed['keywords'] = [
                DataProcessor.clean_text(k) for k in keywords if k
            ]
        else:
            processed['keywords'] = []

        # Remove duplicates from keywords
        processed['keywords'] = list(set(processed['keywords']))

        # Ensure at least some keywords
        if not processed['keywords']:
            # Add platform as default keyword
            processed['keywords'] = ['웹소설']

        return processed

    @staticmethod
    def process_batch(novels: List[Dict[str, Any]],
                     remove_duplicates: bool = True) -> List[Dict[str, Any]]:
        """
        Process a batch of novels

        Args:
            novels: List of raw novel data
            remove_duplicates: Whether to remove duplicate novels

        Returns:
            List of processed and validated novels
        """
        logger.info(f"Processing {len(novels)} novels...")

        processed_novels = []
        seen_titles = set()

        for novel in novels:
            # Process the novel
            processed = DataProcessor.process_novel(novel)

            # Validate
            if not DataProcessor.validate_novel(processed):
                logger.warning(f"Skipping invalid novel: {processed.get('title', 'Unknown')}")
                continue

            # Check for duplicates
            if remove_duplicates:
                title_key = f"{processed['title']}_{processed['author']}"
                if title_key in seen_titles:
                    logger.debug(f"Skipping duplicate: {processed['title']}")
                    continue
                seen_titles.add(title_key)

            processed_novels.append(processed)

        logger.info(f"Processed {len(processed_novels)} valid novels")

        if remove_duplicates:
            removed = len(novels) - len(processed_novels)
            logger.info(f"Removed {removed} invalid/duplicate novels")

        return processed_novels

    @staticmethod
    def deduplicate_by_url(novels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate novels by URL

        Args:
            novels: List of novels

        Returns:
            Deduplicated list
        """
        seen_urls = set()
        unique_novels = []

        for novel in novels:
            url = novel.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_novels.append(novel)

        logger.info(f"Deduplicated: {len(novels)} -> {len(unique_novels)} novels")
        return unique_novels
