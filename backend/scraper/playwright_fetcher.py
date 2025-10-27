"""
Playwright-based fetcher for JavaScript-rendered content.
Handles modern SPAs and dynamically-loaded content including PDF links.
"""
import asyncio
from typing import Optional, Dict, List
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

from ..config import get_settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class PlaywrightFetcher:
    """Async browser automation client for JavaScript-rendered sites."""
    
    def __init__(self):
        """Initialize the Playwright fetcher."""
        settings = get_settings()
        self.timeout = settings.playwright_timeout
        self.wait_for_selector = settings.playwright_wait_for_selector
        self.headless = settings.playwright_headless
        self.user_agent = settings.user_agent
        self.rate_limit_delay = settings.rate_limit_delay
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self._initialized = False
    
    async def initialize(self):
        """Start the browser instance."""
        if self._initialized:
            return
        
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']  # Avoid bot detection
            )
            self._initialized = True
            logger.info(f"Playwright browser started (headless={self.headless})")
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            raise
    
    async def close(self):
        """Close the browser and Playwright instance."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False
        logger.info("Playwright browser closed")
    
    async def _extract_links(self, page: Page, base_url: str) -> List[str]:
        """
        Extract all links from a page, including JavaScript-loaded ones.
        
        Args:
            page: Playwright page object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of absolute URLs
        """
        try:
            # Wait a bit for any lazy-loaded content
            await asyncio.sleep(0.5)
            
            # Extract all href attributes
            links = await page.evaluate('''
                () => {
                    const anchors = Array.from(document.querySelectorAll('a[href]'));
                    return anchors.map(a => a.href);
                }
            ''')
            
            # Convert to absolute URLs
            absolute_links = []
            for link in links:
                try:
                    absolute_url = urljoin(base_url, link)
                    absolute_links.append(absolute_url)
                except Exception:
                    continue
            
            return list(set(absolute_links))  # Remove duplicates
        except Exception as e:
            logger.warning(f"Error extracting links: {e}")
            return []
    
    async def _get_pdf_links(self, page: Page, base_url: str) -> List[str]:
        """
        Find all PDF links on the page.
        
        Args:
            page: Playwright page object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of PDF URLs
        """
        try:
            # Find links ending with .pdf or containing pdf in the URL
            pdf_links = await page.evaluate('''
                () => {
                    const anchors = Array.from(document.querySelectorAll('a[href]'));
                    return anchors
                        .map(a => a.href)
                        .filter(href => 
                            href.toLowerCase().endsWith('.pdf') || 
                            href.toLowerCase().includes('/pdf/') ||
                            href.toLowerCase().includes('=pdf')
                        );
                }
            ''')
            
            # Convert to absolute URLs
            absolute_pdfs = []
            for link in pdf_links:
                try:
                    absolute_url = urljoin(base_url, link)
                    absolute_pdfs.append(absolute_url)
                except Exception:
                    continue
            
            if absolute_pdfs:
                logger.info(f"Found {len(absolute_pdfs)} PDF links")
            
            return list(set(absolute_pdfs))
        except Exception as e:
            logger.warning(f"Error finding PDF links: {e}")
            return []
    
    async def fetch(
        self,
        url: str,
        wait_for_network_idle: bool = True,
        respect_robots: bool = True
    ) -> Optional[Dict[str, any]]:
        """
        Fetch a URL with full JavaScript execution.
        
        Args:
            url: URL to fetch
            wait_for_network_idle: Wait for network to be idle before extracting
            respect_robots: Whether to respect robots.txt (checked separately)
            
        Returns:
            Dictionary with status_code, content, headers, links, or None on failure
        """
        if not self._initialized:
            await self.initialize()
        
        # Rate limiting
        await asyncio.sleep(self.rate_limit_delay)
        
        page = None
        try:
            # Create a new page
            page = await self.browser.new_page(
                user_agent=self.user_agent
            )
            
            # Set viewport to avoid mobile rendering
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Navigate to URL
            logger.info(f"Playwright fetching: {url}")
            response = await page.goto(
                url,
                wait_until='networkidle' if wait_for_network_idle else 'domcontentloaded',
                timeout=self.timeout
            )
            
            if response is None:
                logger.warning(f"No response from {url}")
                return None
            
            # Wait for the body element to ensure page is loaded
            try:
                await page.wait_for_selector(self.wait_for_selector, timeout=5000)
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout waiting for selector '{self.wait_for_selector}' on {url}")
            
            # Extract content
            content = await page.content()
            
            # Extract links
            links = await self._extract_links(page, url)
            
            # Extract PDF links specifically
            pdf_links = await self._get_pdf_links(page, url)
            
            # Get final URL (after any redirects)
            final_url = page.url
            
            result = {
                "status_code": response.status,
                "content": content,
                "headers": dict(response.headers),
                "url": final_url,
                "links": links,
                "pdf_links": pdf_links
            }
            
            logger.info(f"Playwright fetched {url}: {len(content)} chars, {len(links)} links, {len(pdf_links)} PDFs")
            return result
            
        except PlaywrightTimeoutError:
            logger.warning(f"Playwright timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Playwright error fetching {url}: {e}")
            # Try to take screenshot for debugging
            if page:
                try:
                    screenshot_path = f"error_{urlparse(url).netloc}.png"
                    await page.screenshot(path=screenshot_path)
                    logger.info(f"Screenshot saved to {screenshot_path}")
                except Exception:
                    pass
            return None
        finally:
            if page:
                await page.close()
    
    async def fetch_multiple(
        self,
        urls: List[str],
        max_concurrent: int = 3  # Lower than httpx to avoid browser overload
    ) -> Dict[str, Optional[Dict]]:
        """
        Fetch multiple URLs concurrently with browser automation.
        
        Args:
            urls: List of URLs to fetch
            max_concurrent: Maximum concurrent browser tabs
            
        Returns:
            Dictionary mapping URLs to fetch results
        """
        if not self._initialized:
            await self.initialize()
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(url):
            async with semaphore:
                return url, await self.fetch(url)
        
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        return dict(results)

