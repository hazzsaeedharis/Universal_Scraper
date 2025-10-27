"""
Pydantic schemas for API request/response validation.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# Scraping schemas
class DirectScrapeRequest(BaseModel):
    """Request to scrape a specific URL."""
    url: str = Field(..., description="URL to scrape")
    max_depth: Optional[int] = Field(3, description="Maximum crawl depth")
    max_pages: Optional[int] = Field(100, description="Maximum pages to scrape")


class SmartScrapeRequest(BaseModel):
    """Request for AI-powered scraping."""
    query: str = Field(..., description="Natural language query")
    max_sites: Optional[int] = Field(3, description="Maximum number of sites to scrape")
    max_pages_per_site: Optional[int] = Field(50, description="Max pages per site")


class JobResponse(BaseModel):
    """Response with job information."""
    job_id: int
    status: str
    message: str


class JobStatus(BaseModel):
    """Job status information."""
    job_id: int
    status: str
    job_type: str
    name: Optional[str] = None
    query: Optional[str] = None
    start_url: Optional[str] = None
    urls_discovered: int
    urls_scraped: int
    urls_failed: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# Search schemas
class SearchRequest(BaseModel):
    """RAG search request."""
    query: str = Field(..., description="Search query")
    top_k: Optional[int] = Field(10, description="Number of results")
    namespace: Optional[str] = Field("", description="Namespace to search")


class SearchResult(BaseModel):
    """Single search result."""
    text: str
    score: float
    source: Dict[str, Any]
    id: str


class SearchResponse(BaseModel):
    """Search response."""
    query: str
    results: List[SearchResult]
    count: int
    response_time_ms: float


# Statistics schemas
class StatsResponse(BaseModel):
    """System statistics."""
    total_jobs: int
    total_urls_scraped: int
    total_domains: int
    vector_store_stats: Dict[str, Any]
    storage_stats: Dict[str, Any]


class DomainInfo(BaseModel):
    """Domain information."""
    domain: str
    file_count: int
    total_size: int

