"""
API Routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from collections import Counter
import uuid

from backend.app.models import (
    SearchRequest,
    SearchResponse,
    NovelDetailResponse,
    PopularKeywordsResponse,
    NovelInput
)
from backend.app.services.vector_db import vector_db_service
from backend.app.config import settings

router = APIRouter(prefix="/v1", tags=["novels"])


@router.post("/novels/search", response_model=SearchResponse)
async def search_novels(request: SearchRequest):
    """
    Search novels based on natural language query

    Args:
        request: Search request with query and limit

    Returns:
        Search results with similar novels
    """
    try:
        # Validate query length
        if len(request.query) > settings.max_query_length:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_QUERY",
                    "message": f"쿼리는 {settings.max_query_length}자를 초과할 수 없습니다"
                }
            )

        # Search for similar novels
        results = vector_db_service.search_novels(
            query=request.query,
            limit=request.limit
        )

        # Generate search ID
        search_id = str(uuid.uuid4())

        return SearchResponse(
            status="success",
            data={
                "query": request.query,
                "results": results,
                "total_results": len(results),
                "search_id": search_id
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SERVER_ERROR",
                "message": "서버 내부 오류가 발생했습니다",
                "details": str(e)
            }
        )


@router.get("/novels/{novel_id}", response_model=NovelDetailResponse)
async def get_novel_detail(novel_id: int):
    """
    Get detailed information about a specific novel

    Args:
        novel_id: Novel ID

    Returns:
        Detailed novel information
    """
    try:
        novel = vector_db_service.get_novel_by_id(novel_id)

        if not novel:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": "요청한 소설을 찾을 수 없습니다"
                }
            )

        return NovelDetailResponse(
            status="success",
            data=novel
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SERVER_ERROR",
                "message": "서버 내부 오류가 발생했습니다",
                "details": str(e)
            }
        )


@router.get("/keywords/popular", response_model=PopularKeywordsResponse)
async def get_popular_keywords(limit: int = Query(default=20, ge=1, le=100)):
    """
    Get popular keywords from all novels

    Args:
        limit: Number of keywords to return

    Returns:
        List of popular keywords with counts
    """
    try:
        # Get all novels
        all_novels = vector_db_service.get_all_novels()

        # Collect all keywords
        all_keywords = []
        for novel in all_novels:
            all_keywords.extend(novel.get("keywords", []))

        # Count keyword frequency
        keyword_counts = Counter(all_keywords)
        popular_keywords = [
            {"keyword": keyword, "count": count}
            for keyword, count in keyword_counts.most_common(limit)
        ]

        return PopularKeywordsResponse(
            status="success",
            data={
                "keywords": popular_keywords
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SERVER_ERROR",
                "message": "서버 내부 오류가 발생했습니다",
                "details": str(e)
            }
        )


@router.get("/novels", response_model=SearchResponse)
async def get_novels(
    platform: str = Query(None, description="플랫폼명으로 필터링"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100)
):
    """
    Get list of novels with optional platform filtering

    Args:
        platform: Platform name to filter by
        page: Page number
        limit: Items per page

    Returns:
        List of novels with pagination
    """
    try:
        all_novels = vector_db_service.get_all_novels()

        # Filter by platform if specified
        if platform:
            all_novels = [n for n in all_novels if n["platform"] == platform]

        # Pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_novels = all_novels[start_idx:end_idx]

        total_items = len(all_novels)
        total_pages = (total_items + limit - 1) // limit

        return SearchResponse(
            status="success",
            data={
                "novels": paginated_novels,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total_items,
                    "items_per_page": limit
                }
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SERVER_ERROR",
                "message": "서버 내부 오류가 발생했습니다",
                "details": str(e)
            }
        )


@router.get("/novels/{novel_id}/similar", response_model=SearchResponse)
async def get_similar_novels(novel_id: int, limit: int = Query(default=10, ge=1, le=50)):
    """
    Get novels similar to a specific novel

    Args:
        novel_id: Base novel ID
        limit: Number of similar novels to return

    Returns:
        List of similar novels
    """
    try:
        # Get the base novel
        base_novel = vector_db_service.get_novel_by_id(novel_id)

        if not base_novel:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": "요청한 소설을 찾을 수 없습니다"
                }
            )

        # Use the novel's description and keywords as search query
        query = f"{base_novel['title']} {base_novel['description']} {' '.join(base_novel['keywords'])}"
        similar_novels = vector_db_service.search_novels(query, limit=limit + 1)

        # Remove the base novel from results
        similar_novels = [n for n in similar_novels if n["id"] != novel_id][:limit]

        return SearchResponse(
            status="success",
            data={
                "base_novel": {
                    "id": base_novel["id"],
                    "title": base_novel["title"]
                },
                "similar_novels": similar_novels
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SERVER_ERROR",
                "message": "서버 내부 오류가 발생했습니다",
                "details": str(e)
            }
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    novel_count = vector_db_service.count_novels()
    return {
        "status": "healthy",
        "novels_count": novel_count
    }


@router.post("/admin/novels")
async def add_novels(novels: List[NovelInput]):
    """
    Admin endpoint to add novels to the database

    Args:
        novels: List of novels to add

    Returns:
        Success message
    """
    try:
        novel_dicts = [novel.model_dump() for novel in novels]
        vector_db_service.add_novels(novel_dicts)

        return {
            "status": "success",
            "message": f"{len(novels)}개의 소설이 추가되었습니다"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SERVER_ERROR",
                "message": "소설 추가 중 오류가 발생했습니다",
                "details": str(e)
            }
        )