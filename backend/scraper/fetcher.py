"""
HTTP fetcher with retry logic, rate limiting, and robots.txt compliance.
Supports both httpx (fast, static) and Playwright (JavaScript-enabled) methods.
"""
import asyncio
from typing import Optional, Dict
from urllib.parse import urlparse
from enum import Enum
import httpx
from urllib.robotparser import RobotFileParser

from ..config import get_settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ScraperMethod(str, Enum):
    """Enum for scraping method selection."""
    HTTPX = "httpx"
    PLAYWRIGHT = "playwright"


class Fetcher:
    """Async HTTP client with intelligent fetching."""
    
    def __init__(self, method: ScraperMethod = ScraperMethod.HTTPX):
        """
        Initialize the fetcher.
        
        Args:
            method: Scraping method to use (httpx or playwright)
        """
        settings = get_settings()
        self.method = method
        self.timeout = settings.request_timeout
        self.user_agent = settings.user_agent
        self.rate_limit_delay = settings.rate_limit_delay
        self.respect_robots = settings.respect_robots_txt
        self.robots_cache: Dict[str, RobotFileParser] = {}
        
        if not self.respect_robots:
            logger.info("⚠️  robots.txt checking is DISABLED (testing mode)")
        
        # Always create an httpx client (needed for file downloads even with Playwright)
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": self.user_agent}
        )
        
        # Initialize Playwright if using that method
        if method == ScraperMethod.PLAYWRIGHT:
            from .playwright_fetcher import PlaywrightFetcher
            self.playwright_fetcher = PlaywrightFetcher()
            logger.info("Fetcher initialized with Playwright method (httpx available for downloads)")
        else:
            self.playwright_fetcher = None
            logger.info("Fetcher initialized with httpx method")
    
    async def close(self):
        """Close the HTTP client and/or Playwright browser."""
        # Close Playwright if initialized
        if self.method == ScraperMethod.PLAYWRIGHT and self.playwright_fetcher:
            await self.playwright_fetcher.close()
        
        # Always close httpx client (used by both methods)
        if self.client:
            await self.client.aclose()
    
    def _get_robots_url(self, url: str) -> str:
        """Get robots.txt URL for a given URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    
    async def _get_robots_parser(self, domain: str) -> Optional[RobotFileParser]:
        """Get or fetch robots.txt parser for a domain."""
        if domain in self.robots_cache:
            return self.robots_cache[domain]
        
        robots_url = f"https://{domain}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)
        
        try:
            response = await self.client.get(robots_url)
            if response.status_code == 200:
                # Parse robots.txt content
                lines = response.text.split('\n')
                parser.parse(lines)
                self.robots_cache[domain] = parser
                logger.info(f"Loaded robots.txt for {domain}")
                return parser
        except Exception as e:
            logger.warning(f"Could not fetch robots.txt for {domain}: {e}")
        
        # Cache empty parser to avoid repeated requests
        self.robots_cache[domain] = None
        return None
    
    async def can_fetch(self, url: str) -> bool:
        """
        Check if URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed, False otherwise
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        parser = await self._get_robots_parser(domain)
        if parser is None:
            # No robots.txt or error fetching it, allow by default
            return True
        
        return parser.can_fetch(self.user_agent, url)
    
    async def fetch(
        self,
        url: str,
        retry_count: int = 3,
        respect_robots: bool = None
    ) -> Optional[Dict[str, any]]:
        """
        Fetch a URL with retry logic.
        
        Args:
            url: URL to fetch
            retry_count: Number of retries on failure
            respect_robots: Whether to respect robots.txt (None = use global setting)
            
        Returns:
            Dictionary with status_code, content, headers, or None on failure
        """
        # Use global setting if not explicitly provided
        if respect_robots is None:
            respect_robots = self.respect_robots
            
        # Route to appropriate fetcher based on method
        if self.method == ScraperMethod.PLAYWRIGHT:
            return await self._fetch_playwright(url, respect_robots)
        else:
            return await self._fetch_httpx(url, retry_count, respect_robots)
    
    async def _fetch_httpx(
        self,
        url: str,
        retry_count: int = 3,
        respect_robots: bool = True
    ) -> Optional[Dict[str, any]]:
        """
        Fetch a URL using httpx (original method).
        
        Args:
            url: URL to fetch
            retry_count: Number of retries on failure
            respect_robots: Whether to respect robots.txt
            
        Returns:
            Dictionary with status_code, content, headers, or None on failure
        """
        # Check robots.txt
        if respect_robots:
            if not await self.can_fetch(url):
                logger.info(f"Robots.txt disallows fetching: {url}")
                return None
        
        # Rate limiting
        await asyncio.sleep(self.rate_limit_delay)
        
        # Attempt to fetch with retries
        for attempt in range(retry_count):
            try:
                response = await self.client.get(url)
                
                if response.status_code == 200:
                    return {
                        "status_code": response.status_code,
                        "content": response.text,
                        "headers": dict(response.headers),
                        "url": str(response.url),  # Final URL after redirects
                        "pdf_links": []  # httpx doesn't detect PDF links (no JS execution)
                    }
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    if response.status_code in [404, 403, 401]:
                        # Don't retry for these status codes
                        return None
                    
            except httpx.TimeoutException:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1}/{retry_count})")
            except httpx.RequestError as e:
                logger.warning(f"Request error for {url}: {e} (attempt {attempt + 1}/{retry_count})")
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return None
            
            # Wait before retry (exponential backoff)
            if attempt < retry_count - 1:
                await asyncio.sleep(2 ** attempt)
        
        logger.error(f"Failed to fetch {url} after {retry_count} attempts")
        return None
    
    async def _fetch_playwright(
        self,
        url: str,
        respect_robots: bool = True
    ) -> Optional[Dict[str, any]]:
        """
        Fetch a URL using Playwright (JavaScript-enabled).
        
        Args:
            url: URL to fetch
            respect_robots: Whether to respect robots.txt
            
        Returns:
            Dictionary with status_code, content, headers, links, or None on failure
        """
        # Check robots.txt
        if respect_robots:
            if not await self.can_fetch(url):
                logger.info(f"Robots.txt disallows fetching: {url}")
                return None
        
        # Delegate to Playwright fetcher
        return await self.playwright_fetcher.fetch(url, wait_for_network_idle=True, respect_robots=False)
    
    async def download_file(
        self,
        url: str,
        save_path: str,
        respect_robots: bool = None
    ) -> bool:
        """
        Download a binary file (like PDF) from URL.
        
        Args:
            url: URL to download
            save_path: Local path to save the file
            respect_robots: Whether to respect robots.txt (None = use global setting)
            
        Returns:
            True if successful, False otherwise
        """
        # Use global setting if not explicitly provided
        if respect_robots is None:
            respect_robots = self.respect_robots
            
        # Check robots.txt
        if respect_robots:
            if not await self.can_fetch(url):
                logger.info(f"Robots.txt disallows downloading: {url}")
                return False
        
        # Rate limiting
        await asyncio.sleep(self.rate_limit_delay)
        
        try:
            response = await self.client.get(url)
            
            if response.status_code == 200:
                # Write binary content to file
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded {url} to {save_path}")
                return True
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return False
    
    async def fetch_multiple(
        self,
        urls: list,
        max_concurrent: int = 5
    ) -> Dict[str, Optional[Dict]]:
        """
        Fetch multiple URLs concurrently.
        
        Args:
            urls: List of URLs to fetch
            max_concurrent: Maximum concurrent requests
            
        Returns:
            Dictionary mapping URLs to fetch results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(url):
            async with semaphore:
                return url, await self.fetch(url)
        
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        return dict(results)

