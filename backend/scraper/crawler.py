"""
Domain crawler that follows internal links recursively.
"""
import asyncio
import os
import tempfile
import hashlib
from typing import Set, List, Optional, Callable
from urllib.parse import urlparse
from collections import deque

from .fetcher import Fetcher, ScraperMethod
from .parser import Parser
from .pdf_processor import PDFProcessor, PDF_SUPPORT
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
        on_page_callback: Optional[Callable] = None,
        scraper_method: ScraperMethod = ScraperMethod.HTTPX
    ):
        """
        Initialize the crawler.
        
        Args:
            start_url: Starting URL
            max_depth: Maximum crawl depth (None for unlimited)
            max_pages: Maximum pages to crawl (None for unlimited)
            on_page_callback: Callback function called for each page
            scraper_method: Scraping method to use (httpx or playwright)
        """
        settings = get_settings()
        
        self.start_url = normalize_url(start_url)
        self.domain = urlparse(self.start_url).netloc
        self.max_depth = max_depth or settings.max_depth
        self.max_pages = max_pages or 100
        self.on_page_callback = on_page_callback
        self.scraper_method = scraper_method
        
        # State tracking
        self.visited: Set[str] = set()
        self.queue: deque = deque([(self.start_url, 0)])  # (url, depth)
        self.failed: List[dict] = []
        
        # Components
        self.fetcher = Fetcher(method=scraper_method)
        self.parser = Parser()
        
        logger.info(f"Crawler initialized with {scraper_method.value} method")
        
        # PDF processing (if enabled and available)
        self.pdf_enabled = settings.enable_pdf_scraping and PDF_SUPPORT
        if self.pdf_enabled:
            self.pdf_processor = PDFProcessor(
                max_pages=settings.pdf_max_pages,
                max_size_mb=settings.pdf_max_size_mb,
                ocr_languages=settings.ocr_languages
            )
            logger.info("PDF processing enabled")
        else:
            self.pdf_processor = None
            if settings.enable_pdf_scraping and not PDF_SUPPORT:
                logger.warning("PDF processing requested but dependencies not installed")
    
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
            
            # Process the URL (PDF or regular page)
            try:
                # Check if it's a PDF
                if self._is_pdf_url(url):
                    result = await self._process_pdf(url, depth)
                else:
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
                logger.error(f"Error processing {url}: {e}")
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
        
        # Add PDF links to queue (from Playwright detection)
        # PDFs found by Playwright should be processed even if not at max depth
        if response.get('pdf_links') and self.pdf_enabled:
            for pdf_link in response['pdf_links']:
                if pdf_link not in self.visited and is_same_domain(pdf_link, self.start_url):
                    logger.info(f"Queuing detected PDF: {pdf_link}")
                    self.queue.append((pdf_link, depth + 1))
        
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
    
    def _is_pdf_url(self, url: str) -> bool:
        """Check if URL likely points to a PDF."""
        return url.lower().endswith('.pdf')
    
    async def _process_pdf(self, url: str, depth: int) -> Optional[dict]:
        """
        Download and process a PDF file.
        
        Args:
            url: PDF URL
            depth: Current depth
            
        Returns:
            Dictionary with PDF data or None on failure
        """
        if not self.pdf_enabled or not self.pdf_processor:
            logger.warning(f"PDF processing disabled, skipping {url}")
            return None
        
        logger.info(f"Processing PDF: {url}")
        
        # Create temporary file for download
        url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
        temp_path = os.path.join(tempfile.gettempdir(), f"pdf_{url_hash}.pdf")
        
        try:
            # Download PDF (skip robots.txt check for public PDFs)
            success = await self.fetcher.download_file(url, temp_path, respect_robots=False)
            if not success:
                logger.error(f"Failed to download PDF from {url}")
                self.failed.append({"url": url, "error": "Download failed", "depth": depth})
                return None
            
            # Extract text from PDF
            extracted_text = self.pdf_processor.extract_full_text(temp_path)
            
            if not extracted_text:
                logger.warning(f"No text extracted from PDF: {url}")
                self.failed.append({"url": url, "error": "Text extraction failed", "depth": depth})
                return None
            
            # Check if it's a menu
            is_menu = self.pdf_processor.is_menu_pdf(extracted_text)
            
            logger.info(f"✅ PDF processed: {len(extracted_text)} chars, is_menu={is_menu}")
            
            return {
                "url": url,
                "final_url": url,
                "depth": depth,
                "title": f"PDF: {os.path.basename(urlparse(url).path)}",
                "text": extracted_text,
                "html": "",  # No HTML for PDFs
                "links": [],  # Could extract URLs from PDF text if needed
                "metadata": {
                    "content_type": "application/pdf",
                    "is_menu": is_menu
                },
                "word_count": len(extracted_text.split()),
                "status_code": 200,
                "content_type": "pdf"
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF {url}: {e}")
            self.failed.append({"url": url, "error": str(e), "depth": depth})
            return None
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.debug(f"Removed temporary PDF: {temp_path}")
                except Exception as e:
                    logger.warning(f"Could not remove temp file {temp_path}: {e}")
    
    def get_stats(self) -> dict:
        """Get crawl statistics."""
        return {
            "visited": len(self.visited),
            "queued": len(self.queue),
            "failed": len(self.failed),
            "domain": self.domain
        }

