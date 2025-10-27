"""
Configuration management for the Universal Scraper.
Loads settings from environment variables and provides typed configuration objects.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    groq_api_key: str
    pinecone_api_key: str
    
    # Pinecone Configuration
    pinecone_environment: str
    pinecone_index_name: str = "universal-scraper"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./scraper.db"
    
    # Storage
    data_storage_path: str = "./data"
    
    # Scraper Configuration
    max_concurrent_scrapes: int = 5
    max_depth: int = 3
    request_timeout: int = 30
    rate_limit_delay: float = 1.0
    user_agent: str = "UniversalScraper/1.0"
    
    # RAG Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 10
    
    # PDF Processing Configuration
    enable_pdf_scraping: bool = True
    pdf_max_size_mb: int = 50
    pdf_max_pages: int = 20
    enable_ocr: bool = True
    ocr_languages: str = "eng+deu+fra+spa"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

