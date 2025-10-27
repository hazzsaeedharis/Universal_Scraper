"""
Scraping endpoints for direct and smart scraping.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict
import asyncio

from ..schemas import DirectScrapeRequest, SmartScrapeRequest, JobResponse
from ..websocket import manager
from ...storage import get_db, JobType, JobStatus
from ...storage.local_store import get_local_store
from ...scraper import Crawler
from ...scraper.fetcher import ScraperMethod
from ...rag import Chunker, Embedder, VectorStore
from ...ai import SearchAgent, SiteSelector
from ...utils.logger import setup_logger
from ...utils.validators import is_valid_url, get_domain

logger = setup_logger(__name__)
router = APIRouter(prefix="/scrape", tags=["scraping"])


async def process_direct_scrape(job_id: int, url: str, max_depth: int, max_pages: int, scraper_method: str = "httpx"):
    """Background task to process direct scraping."""
    db = get_db()
    local_store = get_local_store()
    
    # Validate and convert scraper_method
    try:
        method = ScraperMethod(scraper_method)
    except ValueError:
        logger.warning(f"Invalid scraper method '{scraper_method}', defaulting to httpx")
        method = ScraperMethod.HTTPX
    
    try:
        # Update job status
        await db.update_job_status(job_id, JobStatus.RUNNING)
        await manager.broadcast_progress(job_id, "running", 0, 0, 0, url)
        
        domain = get_domain(url)
        logger.info(f"Starting direct scrape with {method.value} method: {url}")
        
        # Progress callback
        async def on_page(page_data: Dict):
            # Save to local storage
            try:
                local_path = await local_store.save_content(
                    url=page_data['url'],
                    domain=domain,
                    html=page_data['html'],
                    text=page_data['text'],
                    title=page_data['title'],
                    metadata=page_data['metadata']
                )
                
                # Add to database
                await db.add_scraped_url(
                    job_id=job_id,
                    url=page_data['url'],
                    domain=domain,
                    status="success",
                    title=page_data['title'],
                    content_length=len(page_data['text']),
                    local_path=local_path
                )
                
                # Update job progress
                stats = crawler.get_stats()
                await db.update_job_progress(
                    job_id=job_id,
                    urls_discovered=stats['visited'],
                    urls_scraped=stats['visited'],
                    urls_failed=stats['failed']
                )
                
                # Broadcast progress
                await manager.broadcast_progress(
                    job_id=job_id,
                    status="running",
                    urls_discovered=stats['visited'],
                    urls_scraped=stats['visited'],
                    urls_failed=stats['failed'],
                    current_url=page_data['url']
                )
                
            except Exception as e:
                logger.error(f"Error processing page {page_data['url']}: {e}")
        
        # Create crawler with selected method
        crawler = Crawler(
            start_url=url,
            max_depth=max_depth,
            max_pages=max_pages,
            on_page_callback=on_page,
            scraper_method=method
        )
        
        # Run crawl
        results = await crawler.crawl()
        
        # Process with RAG
        await process_scraped_data_to_rag(job_id, domain)
        
        # Update job as completed
        await db.update_job_status(job_id, JobStatus.COMPLETED)
        await manager.broadcast_completion(
            job_id=job_id,
            status="completed",
            message=f"Successfully scraped {results['pages_crawled']} pages",
            stats=results
        )
        
    except Exception as e:
        logger.error(f"Error in direct scrape job {job_id}: {e}")
        await db.update_job_status(job_id, JobStatus.FAILED, str(e))
        await manager.broadcast_completion(
            job_id=job_id,
            status="failed",
            message=str(e)
        )


async def process_scraped_data_to_rag(job_id: int, domain: str):
    """Process scraped data into RAG pipeline."""
    try:
        db = get_db()
        local_store = get_local_store()
        
        # Get all URLs for this job
        scraped_urls = await db.get_urls_by_job(job_id)
        
        # Initialize RAG components
        chunker = Chunker()
        embedder = Embedder()
        vector_store = VectorStore()
        
        # Ensure index exists
        vector_store.create_index(dimension=embedder.get_dimension())
        
        # Process each scraped URL
        vectors = []
        url_chunk_counts = {}  # Track chunks per URL
        
        for scraped_url in scraped_urls:
            if scraped_url.local_path:
                try:
                    # Load content
                    content = await local_store.load_content(scraped_url.local_path)
                    
                    # Chunk text
                    chunks = chunker.chunk_text(
                        text=content['text'],
                        metadata={
                            'url': scraped_url.url,
                            'title': scraped_url.title,
                            'domain': scraped_url.domain
                        }
                    )
                    
                    # Track chunk count for this URL
                    url_chunk_counts[scraped_url.id] = len(chunks)
                    
                    # Generate embeddings
                    texts = [chunk['text'] for chunk in chunks]
                    embeddings = embedder.embed_batch(texts)
                    
                    # Prepare vectors for Pinecone
                    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                        vector_id = f"{job_id}_{scraped_url.id}_{i}"
                        metadata = {
                            'text': chunk['text'],
                            'url': scraped_url.url,
                            'title': scraped_url.title or '',
                            'domain': scraped_url.domain,
                            'chunk_index': i,
                            'job_id': job_id
                        }
                        vectors.append((vector_id, embedding, metadata))
                    
                    # Update database to mark URL as processed
                    await db.mark_url_as_embedded(
                        url_id=scraped_url.id,
                        chunks_generated=len(chunks)
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing {scraped_url.url}: {e}")
        
        # Upsert to Pinecone
        if vectors:
            vector_store.upsert_vectors(vectors, namespace=f"job_{job_id}")
            logger.info(f"Upserted {len(vectors)} vectors for job {job_id}")
            
            # Update job with total chunks
            total_chunks = sum(url_chunk_counts.values())
            await db.update_job_chunks(job_id, total_chunks)
        
    except Exception as e:
        logger.error(f"Error processing scraped data to RAG: {e}")


@router.post("/direct", response_model=JobResponse)
async def direct_scrape(
    request: DirectScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Scrape a specific URL and follow internal links.
    Supports both httpx (fast, static) and playwright (JavaScript-enabled) methods.
    """
    # Validate URL
    if not is_valid_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    # Validate scraper method
    scraper_method = request.scraper_method or "httpx"
    if scraper_method not in ["httpx", "playwright"]:
        raise HTTPException(status_code=400, detail="Invalid scraper_method. Must be 'httpx' or 'playwright'")
    
    # Create job
    db = get_db()
    job = await db.create_job(
        job_type=JobType.DIRECT,
        start_url=request.url
    )
    
    logger.info(f"Starting direct scrape job {job.id} with {scraper_method} method")
    
    # Start background task
    background_tasks.add_task(
        process_direct_scrape,
        job.id,
        request.url,
        request.max_depth,
        request.max_pages,
        scraper_method
    )
    
    return JobResponse(
        job_id=job.id,
        status="pending",
        message=f"Scraping job started for {request.url} using {scraper_method}"
    )


async def process_smart_scrape(job_id: int, query: str, max_sites: int, max_pages_per_site: int, scraper_method: str = "httpx"):
    """Background task for AI-powered smart scraping."""
    db = get_db()
    
    # Validate and convert scraper_method
    try:
        method = ScraperMethod(scraper_method)
    except ValueError:
        logger.warning(f"Invalid scraper method '{scraper_method}', defaulting to httpx")
        method = ScraperMethod.HTTPX
    
    try:
        await db.update_job_status(job_id, JobStatus.RUNNING)
        await manager.broadcast_progress(job_id, "running", 0, 0, 0, "Analyzing query...")
        
        logger.info(f"Starting smart scrape with {method.value} method: {query}")
        
        # Use AI to generate search queries
        search_agent = SearchAgent()
        queries = search_agent.generate_search_queries(query, num_queries=2)
        
        logger.info(f"Generated search queries: {queries}")
        
        # Simulate search results (in production, integrate with search API)
        # For now, we'll use a placeholder
        await manager.broadcast_progress(
            job_id, "running", 0, 0, 0,
            "Smart scraping requires search API integration. Please use direct scrape for now."
        )
        
        await db.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            "Smart scraping is a placeholder. Use direct scrape with specific URLs."
        )
        
        await manager.broadcast_completion(
            job_id=job_id,
            status="completed",
            message="Smart scraping requires search API integration"
        )
        
    except Exception as e:
        logger.error(f"Error in smart scrape job {job_id}: {e}")
        await db.update_job_status(job_id, JobStatus.FAILED, str(e))
        await manager.broadcast_completion(job_id, "failed", str(e))


@router.post("/smart", response_model=JobResponse)
async def smart_scrape(
    request: SmartScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    AI-powered smart scraping based on natural language query.
    Supports both httpx (fast, static) and playwright (JavaScript-enabled) methods.
    """
    # Validate scraper method
    scraper_method = request.scraper_method or "httpx"
    if scraper_method not in ["httpx", "playwright"]:
        raise HTTPException(status_code=400, detail="Invalid scraper_method. Must be 'httpx' or 'playwright'")
    
    # Create job
    db = get_db()
    job = await db.create_job(
        job_type=JobType.SMART,
        query=request.query
    )
    
    logger.info(f"Starting smart scrape job {job.id} with {scraper_method} method")
    
    # Start background task
    background_tasks.add_task(
        process_smart_scrape,
        job.id,
        request.query,
        request.max_sites,
        request.max_pages_per_site,
        scraper_method
    )
    
    return JobResponse(
        job_id=job.id,
        status="pending",
        message=f"Smart scraping job started for query: {request.query} using {scraper_method}"
    )

