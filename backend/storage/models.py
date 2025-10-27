"""
Database models for the Universal Scraper.
Uses SQLAlchemy for ORM with async support.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

Base = declarative_base()


class JobStatus(str, Enum):
    """Status of a scraping job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Type of scraping job."""
    DIRECT = "direct"  # Direct URL scraping
    SMART = "smart"    # AI-powered search and scrape


class ScrapeJob(Base):
    """Model for scraping jobs."""
    __tablename__ = "scrape_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(SQLEnum(JobType), nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    
    # Job details
    name = Column(String(255), nullable=True)  # Custom job name
    query = Column(Text, nullable=True)  # For smart scraping
    start_url = Column(String(500), nullable=True)  # For direct scraping
    scraper_method = Column(String(20), default="httpx", nullable=False)  # httpx or playwright
    
    # Progress tracking
    urls_discovered = Column(Integer, default=0)
    urls_scraped = Column(Integer, default=0)
    urls_failed = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Results
    total_chunks = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)


class ScrapedURL(Base):
    """Model for individual scraped URLs."""
    __tablename__ = "scraped_urls"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=False, index=True)
    
    # URL details
    url = Column(String(500), nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    
    # Content metadata
    title = Column(String(500), nullable=True)
    content_length = Column(Integer, nullable=True)
    content_type = Column(String(100), nullable=True)
    
    # Status
    status = Column(String(50), nullable=False)  # success, failed, skipped
    error_message = Column(Text, nullable=True)
    
    # Storage
    local_path = Column(String(500), nullable=True)
    
    # Timestamps
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Processing
    chunks_generated = Column(Integer, default=0)
    embedded = Column(Integer, default=0)  # Boolean as int (0 or 1)


class SearchQuery(Base):
    """Model for tracking search queries."""
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Query details
    query_text = Column(Text, nullable=False)
    
    # Results
    results_count = Column(Integer, nullable=True)
    
    # Performance
    response_time_ms = Column(Float, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

