"""
Local file storage for scraped content.
Organizes files by domain and timestamp.
"""
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Optional
import json
import hashlib

from ..config import get_settings
from ..utils.logger import setup_logger
from ..utils.validators import sanitize_filename

logger = setup_logger(__name__)


class LocalStore:
    """Manager for local file storage."""
    
    def __init__(self):
        """Initialize the local storage."""
        settings = get_settings()
        self.base_path = Path(settings.data_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_domain_path(self, domain: str) -> Path:
        """Get the storage path for a domain."""
        safe_domain = sanitize_filename(domain)
        domain_path = self.base_path / safe_domain
        domain_path.mkdir(parents=True, exist_ok=True)
        return domain_path
    
    def _generate_filename(self, url: str) -> str:
        """Generate a filename from a URL."""
        # Use hash to create a unique, filesystem-safe filename
        url_hash = hashlib.md5(url.encode()).hexdigest()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{url_hash}.json"
    
    async def save_content(
        self,
        url: str,
        domain: str,
        html: str,
        text: str,
        title: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Save scraped content to local storage.
        
        Args:
            url: The scraped URL
            domain: The domain of the URL
            html: Raw HTML content
            text: Extracted text content
            title: Page title
            metadata: Additional metadata
            
        Returns:
            Relative path to the saved file
        """
        domain_path = self._get_domain_path(domain)
        filename = self._generate_filename(url)
        file_path = domain_path / filename
        
        # Prepare data structure
        data = {
            "url": url,
            "domain": domain,
            "title": title,
            "html": html,
            "text": text,
            "metadata": metadata or {},
            "scraped_at": datetime.utcnow().isoformat()
        }
        
        # Save as JSON
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
        
        # Return relative path
        relative_path = str(file_path.relative_to(self.base_path))
        logger.info(f"Saved content for {url} to {relative_path}")
        return relative_path
    
    async def load_content(self, relative_path: str) -> dict:
        """
        Load scraped content from storage.
        
        Args:
            relative_path: Relative path to the file
            
        Returns:
            Dictionary with scraped data
        """
        file_path = self.base_path / relative_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"Content file not found: {relative_path}")
        
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content)
    
    async def save_raw_text(
        self,
        domain: str,
        filename: str,
        text: str
    ) -> str:
        """
        Save raw text content.
        
        Args:
            domain: Domain name
            filename: Filename
            text: Text content
            
        Returns:
            Relative path to saved file
        """
        domain_path = self._get_domain_path(domain)
        safe_filename = sanitize_filename(filename)
        file_path = domain_path / safe_filename
        
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(text)
        
        relative_path = str(file_path.relative_to(self.base_path))
        logger.info(f"Saved raw text to {relative_path}")
        return relative_path
    
    def get_domain_stats(self, domain: str) -> dict:
        """
        Get statistics for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            Dictionary with statistics
        """
        domain_path = self._get_domain_path(domain)
        
        if not domain_path.exists():
            return {"file_count": 0, "total_size": 0}
        
        files = list(domain_path.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)
        
        return {
            "file_count": len(files),
            "total_size": total_size
        }
    
    def list_domains(self) -> list:
        """
        List all stored domains.
        
        Returns:
            List of domain names
        """
        if not self.base_path.exists():
            return []
        
        return [d.name for d in self.base_path.iterdir() if d.is_dir()]


# Singleton instance
_store: Optional[LocalStore] = None


def get_local_store() -> LocalStore:
    """Get or create the local store instance."""
    global _store
    if _store is None:
        _store = LocalStore()
    return _store

