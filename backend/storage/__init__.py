"""Storage layer for the Universal Scraper."""
from .models import ScrapeJob, ScrapedURL, SearchQuery, JobStatus, JobType
from .metadata_db import MetadataDB, get_db
from .local_store import LocalStore, get_local_store

__all__ = [
    'ScrapeJob',
    'ScrapedURL',
    'SearchQuery',
    'JobStatus',
    'JobType',
    'MetadataDB',
    'get_db',
    'LocalStore',
    'get_local_store'
]

