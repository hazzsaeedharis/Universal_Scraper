"""Utility modules for the Universal Scraper."""
from .logger import setup_logger, app_logger
from .validators import (
    is_valid_url,
    normalize_url,
    get_domain,
    is_same_domain,
    resolve_url,
    sanitize_filename
)

__all__ = [
    'setup_logger',
    'app_logger',
    'is_valid_url',
    'normalize_url',
    'get_domain',
    'is_same_domain',
    'resolve_url',
    'sanitize_filename'
]

