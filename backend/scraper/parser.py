"""
HTML parser for extracting clean text and links.
"""
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from ..utils.logger import setup_logger
from ..utils.validators import is_valid_url, normalize_url

logger = setup_logger(__name__)


class Parser:
    """HTML content parser."""
    
    def __init__(self):
        """Initialize the parser."""
        # Tags to ignore when extracting text
        self.ignored_tags = [
            'script', 'style', 'meta', 'link', 'noscript',
            'header', 'footer', 'nav', 'aside', 'svg'
        ]
    
    def parse(self, html: str, base_url: str) -> Dict:
        """
        Parse HTML content.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            Dictionary with parsed content
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract clean text
        text = self._extract_text(soup)
        
        # Extract links
        links = self._extract_links(soup, base_url)
        
        # Extract metadata
        metadata = self._extract_metadata(soup)
        
        return {
            "title": title,
            "text": text,
            "links": links,
            "metadata": metadata,
            "word_count": len(text.split()) if text else 0
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        # Try <title> tag
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        
        # Try og:title meta tag
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
        # Try h1 tag
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return None
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text from HTML."""
        # Remove ignored tags
        for tag in self.ignored_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        text = '\n'.join(lines)
        
        # Replace multiple spaces with single space
        text = ' '.join(text.split())
        
        return text
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract and resolve all links."""
        links = []
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            
            # Skip certain types of links
            if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
            
            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            
            # Validate and normalize
            if is_valid_url(absolute_url):
                try:
                    normalized = normalize_url(absolute_url)
                    if normalized not in links:
                        links.append(normalized)
                except Exception as e:
                    logger.debug(f"Could not normalize URL {absolute_url}: {e}")
        
        return links
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from HTML."""
        metadata = {}
        
        # Description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            metadata['description'] = desc_tag['content']
        
        # Keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag and keywords_tag.get('content'):
            metadata['keywords'] = keywords_tag['content']
        
        # Author
        author_tag = soup.find('meta', attrs={'name': 'author'})
        if author_tag and author_tag.get('content'):
            metadata['author'] = author_tag['content']
        
        # Open Graph
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        for tag in og_tags:
            prop = tag.get('property')
            content = tag.get('content')
            if prop and content:
                metadata[prop] = content
        
        return metadata
    
    def extract_main_content(self, html: str) -> str:
        """
        Extract main content (heuristic-based).
        Tries to find the main article/content area.
        
        Args:
            html: HTML content
            
        Returns:
            Extracted text
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Try common content containers
        content_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.content',
            '.main-content',
            '#content',
            '#main-content'
        ]
        
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                return self._extract_text(content)
        
        # Fallback to body
        body = soup.find('body')
        if body:
            return self._extract_text(body)
        
        return self._extract_text(soup)

