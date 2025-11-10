"""
Pydantic Models for Request/Response
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


class SearchRequest(BaseModel):
    """Request model for novel search"""
    query: str = Field(..., min_length=1, max_length=140, description="검색 쿼리 (최대 140자)")
    limit: int = Field(default=10, ge=1, le=50, description="반환할 결과 개수")

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("쿼리는 비어있을 수 없습니다")
        return v.strip()


class NovelResult(BaseModel):
    """Novel search result"""
    id: int
    title: str
    author: str
    description: str
    platform: str
    url: str
    similarity_score: float
    keywords: List[str]


class SearchResponse(BaseModel):
    """Response model for novel search"""
    status: str = "success"
    data: dict


class NovelDetail(BaseModel):
    """Detailed novel information"""
    id: int
    title: str
    author: str
    description: str
    platform: str
    url: str
    keywords: List[str]
    created_at: datetime
    updated_at: datetime


class NovelDetailResponse(BaseModel):
    """Response model for novel detail"""
    status: str = "success"
    data: NovelDetail


class KeywordItem(BaseModel):
    """Keyword with count"""
    keyword: str
    count: int


class PopularKeywordsResponse(BaseModel):
    """Response model for popular keywords"""
    status: str = "success"
    data: dict


class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = "error"
    error: dict


class NovelInput(BaseModel):
    """Input model for adding new novels"""
    title: str
    author: str
    description: str
    platform: str
    url: str
    keywords: List[str]
