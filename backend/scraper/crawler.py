"""
Domain crawler that follows internal links recursively.
"""
import asyncio
from typing import Set, List, Optional, Callable
from urllib.parse import urlparse
from collections import deque

from .fetcher import Fetcher
from .parser import Parser
from ..config import get_settings
from ..utils.logger import setup_logger
from ..utils.validators import is_same_domain, normalize_url

logger = setup_logger(__name__)


class Crawler:
    """Recursive domain crawler."""
    
    def __init__(
        self,
        start_url: str,
        max_depth: Optional[int] = None,
        max_pages: Optional[int] = None,
        on_page_callback: Optional[Callable] = None
    ):
        """
        Initialize the crawler.
        
        Args:
            start_url: Starting URL
            max_depth: Maximum crawl depth (None for unlimited)
            max_pages: Maximum pages to crawl (None for unlimited)
            on_page_callback: Callback function called for each page
        """
        settings = get_settings()
        
        self.start_url = normalize_url(start_url)
        self.domain = urlparse(self.start_url).netloc
        self.max_depth = max_depth or settings.max_depth
        self.max_pages = max_pages or 100
        self.on_page_callback = on_page_callback
        
        # State tracking
        self.visited: Set[str] = set()
        self.queue: deque = deque([(self.start_url, 0)])  # (url, depth)
        self.failed: List[dict] = []
        
        # Components
        self.fetcher = Fetcher()
        self.parser = Parser()
    
    async def crawl(self) -> dict:
        """
        Start crawling.
        
        Returns:
            Dictionary with crawl statistics
        """
        logger.info(f"Starting crawl of {self.start_url} (max_depth={self.max_depth}, max_pages={self.max_pages})")
        
        pages_crawled = 0
        
        while self.queue and pages_crawled < self.max_pages:
            url, depth = self.queue.popleft()
            
            # Skip if already visited
            if url in self.visited:
                continue
            
            # Skip if max depth exceeded
            if depth > self.max_depth:
                continue
            
            # Mark as visited
            self.visited.add(url)
            
            # Fetch the page
            try:
                result = await self._crawl_page(url, depth)
                if result:
                    pages_crawled += 1
                    
                    # Call callback if provided
                    if self.on_page_callback:
                        try:
                            await self.on_page_callback(result)
                        except Exception as e:
                            logger.error(f"Callback error for {url}: {e}")
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                self.failed.append({"url": url, "error": str(e), "depth": depth})
        
        await self.fetcher.close()
        
        return {
            "pages_crawled": pages_crawled,
            "pages_failed": len(self.failed),
            "urls_discovered": len(self.visited),
            "failed_urls": self.failed
        }
    
    async def _crawl_page(self, url: str, depth: int) -> Optional[dict]:
        """
        Crawl a single page.
        
        Args:
            url: URL to crawl
            depth: Current depth
            
        Returns:
            Dictionary with page data or None on failure
        """
        logger.info(f"Crawling {url} (depth={depth})")
        
        # Fetch the page
        response = await self.fetcher.fetch(url)
        if not response:
            self.failed.append({"url": url, "error": "Fetch failed", "depth": depth})
            return None
        
        # Parse the content
        parsed = self.parser.parse(response['content'], url)
        
        # Add links to queue if not at max depth
        if depth < self.max_depth:
            for link in parsed['links']:
                # Only follow same-domain links
                if is_same_domain(link, self.start_url):
                    if link not in self.visited:
                        self.queue.append((link, depth + 1))
        
        return {
            "url": url,
            "final_url": response['url'],
            "depth": depth,
            "title": parsed['title'],
            "text": parsed['text'],
            "html": response['content'],
            "links": parsed['links'],
            "metadata": parsed['metadata'],
            "word_count": parsed['word_count'],
            "status_code": response['status_code']
        }
    
    def get_stats(self) -> dict:
        """Get crawl statistics."""
        return {
            "visited": len(self.visited),
            "queued": len(self.queue),
            "failed": len(self.failed),
            "domain": self.domain
        }

