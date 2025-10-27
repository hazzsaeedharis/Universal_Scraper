"""
Job management endpoints.
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional

from ..schemas import JobStatus as JobStatusSchema, StatsResponse
from ..websocket import manager
from ...storage import get_db, JobStatus
from ...storage.local_store import get_local_store
from ...rag import VectorStore
from ...utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=List[JobStatusSchema])
async def list_jobs(
    limit: int = 50,
    status: Optional[str] = None
):
    """
    List scraping jobs.
    """
    try:
        db = get_db()
        
        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = JobStatus[status.upper()]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        jobs = await db.list_jobs(limit=limit, status=status_enum)
        
        return [
            JobStatusSchema(
                job_id=job.id,
                status=job.status.value,
                job_type=job.job_type.value,
                name=job.name,
                query=job.query,
                start_url=job.start_url,
                urls_discovered=job.urls_discovered,
                urls_scraped=job.urls_scraped,
                urls_failed=job.urls_failed,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                error_message=job.error_message
            )
            for job in jobs
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/namespaces")
async def get_namespaces():
    """
    Get list of available namespaces (jobs) in the vector store.
    """
    try:
        vector_store = VectorStore()
        stats = vector_store.get_stats()
        
        namespaces = []
        if stats.get('namespaces'):
            for namespace, data in stats['namespaces'].items():
                # Extract job_id from namespace (format: job_1, job_2, etc.)
                if namespace.startswith('job_'):
                    try:
                        job_id = int(namespace.split('_')[1])
                        namespaces.append({
                            "namespace": namespace,
                            "job_id": job_id,
                            "vector_count": data.get('vector_count', 0)
                        })
                    except (IndexError, ValueError):
                        pass
        
        # Sort by job_id
        namespaces.sort(key=lambda x: x['job_id'])
        
        return {"namespaces": namespaces}
        
    except Exception as e:
        logger.error(f"Error getting namespaces: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{job_id}/name")
async def update_job_name(job_id: int, name: str):
    """
    Update the name of a job.
    """
    try:
        db = get_db()
        
        # Check if job exists
        job = await db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update the name
        await db.update_job_name(job_id, name)
        
        return {"message": f"Job {job_id} name updated successfully", "name": name}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job name: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=JobStatusSchema)
async def get_job(job_id: int):
    """
    Get details of a specific job.
    """
    try:
        db = get_db()
        job = await db.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusSchema(
            job_id=job.id,
            status=job.status.value,
            job_type=job.job_type.value,
            name=job.name,
            query=job.query,
            start_url=job.start_url,
            urls_discovered=job.urls_discovered,
            urls_scraped=job.urls_scraped,
            urls_failed=job.urls_failed,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{job_id}")
async def job_websocket(websocket: WebSocket, job_id: int):
    """
    WebSocket endpoint for real-time job updates.
    """
    await manager.connect(websocket, job_id)
    
    try:
        # Keep connection alive
        while True:
            # Wait for messages (ping/pong)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)


@router.get("/{job_id}/urls")
async def get_job_urls(job_id: int):
    """
    Get all scraped URLs for a job.
    """
    try:
        db = get_db()
        
        # Check job exists
        job = await db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        urls = await db.get_urls_by_job(job_id)
        
        return {
            "job_id": job_id,
            "urls": [
                {
                    "url": url.url,
                    "domain": url.domain,
                    "title": url.title,
                    "status": url.status,
                    "content_length": url.content_length,
                    "scraped_at": url.scraped_at.isoformat(),
                    "error_message": url.error_message
                }
                for url in urls
            ],
            "total": len(urls)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting URLs for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview", response_model=StatsResponse)
async def get_stats():
    """
    Get system statistics.
    """
    try:
        db = get_db()
        local_store = get_local_store()
        vector_store = VectorStore()
        
        # Get database stats
        all_jobs = await db.list_jobs(limit=10000)
        total_urls_scraped = sum(job.urls_scraped for job in all_jobs)
        
        # Get storage stats
        domains = local_store.list_domains()
        domain_stats = [
            local_store.get_domain_stats(domain)
            for domain in domains
        ]
        total_storage = sum(stats['total_size'] for stats in domain_stats)
        
        # Get vector store stats
        try:
            vs_stats = vector_store.get_stats()
        except Exception as e:
            logger.warning(f"Could not get vector store stats: {e}")
            vs_stats = {}
        
        return StatsResponse(
            total_jobs=len(all_jobs),
            total_urls_scraped=total_urls_scraped,
            total_domains=len(domains),
            vector_store_stats=vs_stats,
            storage_stats={
                "domains": len(domains),
                "total_size_bytes": total_storage
            }
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

