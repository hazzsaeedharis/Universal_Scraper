"""
RAG search endpoints.
"""
from fastapi import APIRouter, HTTPException
import time

from ..schemas import SearchRequest, SearchResponse, SearchResult
from ...rag import Retriever
from ...storage import get_db
from ...utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Perform semantic search over scraped content.
    """
    try:
        # Initialize retriever
        retriever = Retriever()
        
        # Perform search
        results = await retriever.search(
            query=request.query,
            top_k=request.top_k,
            namespace=request.namespace
        )
        
        # Log search query
        db = get_db()
        await db.log_search_query(
            query_text=request.query,
            results_count=results['count'],
            response_time_ms=results['response_time_ms']
        )
        
        return SearchResponse(**results)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_search_history(limit: int = 10):
    """
    Get recent search queries.
    """
    try:
        db = get_db()
        searches = await db.get_recent_searches(limit=limit)
        
        return {
            "searches": [
                {
                    "query": s.query_text,
                    "results_count": s.results_count,
                    "response_time_ms": s.response_time_ms,
                    "created_at": s.created_at.isoformat()
                }
                for s in searches
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching search history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

