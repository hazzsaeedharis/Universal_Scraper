"""
Database operations for metadata storage.
Handles job tracking, URL management, and search history.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update, func
from contextlib import asynccontextmanager

from .models import Base, ScrapeJob, ScrapedURL, SearchQuery, JobStatus, JobType
from ..config import get_settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class MetadataDB:
    """Database manager for scraping metadata."""
    
    def __init__(self):
        """Initialize the database connection."""
        settings = get_settings()
        self.engine = create_async_engine(
            settings.database_url,
            echo=False,
            future=True
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def initialize(self):
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    
    @asynccontextmanager
    async def get_session(self):
        """Get a database session."""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    # Job operations
    async def create_job(
        self,
        job_type: JobType,
        query: Optional[str] = None,
        start_url: Optional[str] = None
    ) -> ScrapeJob:
        """Create a new scraping job."""
        async with self.get_session() as session:
            job = ScrapeJob(
                job_type=job_type,
                query=query,
                start_url=start_url,
                status=JobStatus.PENDING
            )
            session.add(job)
            await session.flush()
            await session.refresh(job)
            logger.info(f"Created job {job.id} of type {job_type}")
            return job
    
    async def get_job(self, job_id: int) -> Optional[ScrapeJob]:
        """Get a job by ID."""
        async with self.get_session() as session:
            result = await session.execute(
                select(ScrapeJob).where(ScrapeJob.id == job_id)
            )
            return result.scalar_one_or_none()
    
    async def update_job_status(
        self,
        job_id: int,
        status: JobStatus,
        error_message: Optional[str] = None
    ):
        """Update job status."""
        async with self.get_session() as session:
            update_data = {"status": status}
            
            if status == JobStatus.RUNNING and not await self._job_started(session, job_id):
                update_data["started_at"] = datetime.utcnow()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                update_data["completed_at"] = datetime.utcnow()
            
            if error_message:
                update_data["error_message"] = error_message
            
            await session.execute(
                update(ScrapeJob)
                .where(ScrapeJob.id == job_id)
                .values(**update_data)
            )
            logger.info(f"Updated job {job_id} status to {status}")
    
    async def _job_started(self, session: AsyncSession, job_id: int) -> bool:
        """Check if job has been started."""
        result = await session.execute(
            select(ScrapeJob.started_at).where(ScrapeJob.id == job_id)
        )
        started_at = result.scalar_one_or_none()
        return started_at is not None
    
    async def update_job_progress(
        self,
        job_id: int,
        urls_discovered: Optional[int] = None,
        urls_scraped: Optional[int] = None,
        urls_failed: Optional[int] = None
    ):
        """Update job progress counters."""
        async with self.get_session() as session:
            update_data = {}
            if urls_discovered is not None:
                update_data["urls_discovered"] = urls_discovered
            if urls_scraped is not None:
                update_data["urls_scraped"] = urls_scraped
            if urls_failed is not None:
                update_data["urls_failed"] = urls_failed
            
            if update_data:
                await session.execute(
                    update(ScrapeJob)
                    .where(ScrapeJob.id == job_id)
                    .values(**update_data)
                )
    
    async def list_jobs(
        self,
        limit: int = 50,
        status: Optional[JobStatus] = None
    ) -> List[ScrapeJob]:
        """List scraping jobs."""
        async with self.get_session() as session:
            query = select(ScrapeJob).order_by(ScrapeJob.created_at.desc())
            
            if status:
                query = query.where(ScrapeJob.status == status)
            
            query = query.limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())
    
    # URL operations
    async def add_scraped_url(
        self,
        job_id: int,
        url: str,
        domain: str,
        status: str,
        title: Optional[str] = None,
        content_length: Optional[int] = None,
        local_path: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> ScrapedURL:
        """Add a scraped URL record."""
        async with self.get_session() as session:
            scraped_url = ScrapedURL(
                job_id=job_id,
                url=url,
                domain=domain,
                status=status,
                title=title,
                content_length=content_length,
                local_path=local_path,
                error_message=error_message
            )
            session.add(scraped_url)
            await session.flush()
            await session.refresh(scraped_url)
            return scraped_url
    
    async def get_urls_by_job(self, job_id: int) -> List[ScrapedURL]:
        """Get all URLs for a job."""
        async with self.get_session() as session:
            result = await session.execute(
                select(ScrapedURL)
                .where(ScrapedURL.job_id == job_id)
                .order_by(ScrapedURL.scraped_at.desc())
            )
            return list(result.scalars().all())
    
    async def url_exists(self, url: str, job_id: int) -> bool:
        """Check if a URL has already been scraped in this job."""
        async with self.get_session() as session:
            result = await session.execute(
                select(func.count(ScrapedURL.id))
                .where(ScrapedURL.url == url, ScrapedURL.job_id == job_id)
            )
            count = result.scalar_one()
            return count > 0
    
    # Search query operations
    async def log_search_query(
        self,
        query_text: str,
        results_count: int,
        response_time_ms: float
    ) -> SearchQuery:
        """Log a search query."""
        async with self.get_session() as session:
            search_query = SearchQuery(
                query_text=query_text,
                results_count=results_count,
                response_time_ms=response_time_ms
            )
            session.add(search_query)
            await session.flush()
            await session.refresh(search_query)
            return search_query
    
    async def get_recent_searches(self, limit: int = 10) -> List[SearchQuery]:
        """Get recent search queries."""
        async with self.get_session() as session:
            result = await session.execute(
                select(SearchQuery)
                .order_by(SearchQuery.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
    
    async def close(self):
        """Close database connections."""
        await self.engine.dispose()
        logger.info("Database connections closed")


# Singleton instance
_db: Optional[MetadataDB] = None


def get_db() -> MetadataDB:
    """Get or create the database instance."""
    global _db
    if _db is None:
        _db = MetadataDB()
    return _db

