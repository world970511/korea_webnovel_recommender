"""
Crawler Utilities

Helper functions and utilities for crawler operations.
"""

import logging
from typing import List, Dict
from backend.app.services.vector_db import vector_db_service

logger = logging.getLogger(__name__)


async def save_crawled_novels(novels: List[Dict]) -> int:
    """
    Save crawled novels to the database.

    Args:
        novels: List of novel dictionaries from crawlers

    Returns:
        Number of novels successfully saved
    """
    if not novels:
        logger.warning("No novels to save")
        return 0

    try:
        # Add novels to vector database
        vector_db_service.add_novels(novels)
        logger.info(f"Successfully saved {len(novels)} novels to database")
        return len(novels)

    except Exception as e:
        logger.error(f"Failed to save novels: {str(e)}")
        return 0


def deduplicate_novels(novels: List[Dict]) -> List[Dict]:
    """
    Remove duplicate novels based on title and author.

    Args:
        novels: List of novel dictionaries

    Returns:
        Deduplicated list of novels
    """
    seen = set()
    unique_novels = []

    for novel in novels:
        # Create unique key from title and author
        key = (
            novel.get("title", "").lower().strip(),
            novel.get("author", "").lower().strip()
        )

        if key not in seen and key[0] and key[1]:
            seen.add(key)
            unique_novels.append(novel)

    removed = len(novels) - len(unique_novels)
    if removed > 0:
        logger.info(f"Removed {removed} duplicate novels")

    return unique_novels


def filter_novels_by_keywords(
    novels: List[Dict],
    required_keywords: List[str] = None,
    excluded_keywords: List[str] = None
) -> List[Dict]:
    """
    Filter novels by keywords.

    Args:
        novels: List of novel dictionaries
        required_keywords: Keywords that must be present (OR logic)
        excluded_keywords: Keywords that must not be present

    Returns:
        Filtered list of novels
    """
    if not required_keywords and not excluded_keywords:
        return novels

    filtered = []

    for novel in novels:
        keywords = [k.lower() for k in novel.get("keywords", [])]

        # Check excluded keywords first
        if excluded_keywords:
            if any(k.lower() in keywords for k in excluded_keywords):
                continue

        # Check required keywords
        if required_keywords:
            if not any(k.lower() in keywords for k in required_keywords):
                continue

        filtered.append(novel)

    logger.info(f"Filtered from {len(novels)} to {len(filtered)} novels")
    return filtered


def merge_novel_lists(*novel_lists: List[Dict]) -> List[Dict]:
    """
    Merge multiple lists of novels and deduplicate.

    Args:
        *novel_lists: Variable number of novel lists

    Returns:
        Merged and deduplicated list
    """
    all_novels = []
    for novel_list in novel_lists:
        all_novels.extend(novel_list)

    return deduplicate_novels(all_novels)


def get_crawl_statistics(novels: List[Dict]) -> Dict:
    """
    Generate statistics from crawled novels.

    Args:
        novels: List of novel dictionaries

    Returns:
        Dictionary with statistics
    """
    if not novels:
        return {
            "total": 0,
            "platforms": {},
            "authors": 0,
            "keywords": {},
        }

    from collections import Counter

    platforms = Counter(n.get("platform", "unknown") for n in novels)
    authors = len(set(n.get("author", "") for n in novels))

    # Count keywords
    all_keywords = []
    for novel in novels:
        all_keywords.extend(novel.get("keywords", []))
    keyword_counts = Counter(all_keywords)

    return {
        "total": len(novels),
        "platforms": dict(platforms),
        "authors": authors,
        "keywords": dict(keyword_counts.most_common(20)),
    }


def validate_novel_data(novel: Dict) -> bool:
    """
    Validate that novel data has required fields.

    Args:
        novel: Novel dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["title", "author", "description", "platform", "url", "keywords"]

    for field in required_fields:
        if field not in novel:
            logger.warning(f"Novel missing required field: {field}")
            return False

        # Check non-empty
        value = novel[field]
        if isinstance(value, str) and not value.strip():
            logger.warning(f"Novel has empty field: {field}")
            return False
        elif isinstance(value, list) and not value:
            logger.warning(f"Novel has empty list for: {field}")
            return False

    return True


def clean_novel_data(novels: List[Dict]) -> List[Dict]:
    """
    Clean and validate novel data, removing invalid entries.

    Args:
        novels: List of novel dictionaries

    Returns:
        Cleaned list of novels
    """
    cleaned = []

    for novel in novels:
        if validate_novel_data(novel):
            cleaned.append(novel)

    removed = len(novels) - len(cleaned)
    if removed > 0:
        logger.warning(f"Removed {removed} invalid novels")

    return cleaned
