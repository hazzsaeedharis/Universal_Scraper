"""
RAG search endpoints.
"""
from fastapi import APIRouter, HTTPException
import time

from ..schemas import SearchRequest, SearchResponse, SearchResult
from ...rag import Retriever, RAGService
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


@router.post("/ai-answer")
async def ai_answer(request: SearchRequest):
    """
    Get an AI-powered answer using RAG (Retrieval-Augmented Generation).
    Retrieves relevant content and generates a natural language answer.
    """
    try:
        # Initialize RAG service
        rag_service = RAGService()
        
        # Generate answer
        result = await rag_service.answer_query(
            query=request.query,
            top_k=request.top_k,
            namespace=request.namespace
        )
        
        # Log search query
        db = get_db()
        await db.log_search_query(
            query_text=request.query,
            results_count=len(result['sources']),
            response_time_ms=result['response_time_ms']
        )
        
        return result
        
    except Exception as e:
        logger.error(f"AI answer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-answer-structured")
async def ai_answer_structured(request: SearchRequest):
    """
    Get an AI-powered answer with structured data extraction.
    Retrieves relevant content, generates a natural language answer,
    and extracts structured data (menus, business hours, contact info, etc.).
    """
    try:
        # Initialize RAG service
        rag_service = RAGService()
        
        # Generate answer with structured extraction
        result = await rag_service.answer_query(
            query=request.query,
            top_k=request.top_k,
            namespace=request.namespace,
            extract_structured=True  # Enable structured extraction
        )
        
        # Log search query
        db = get_db()
        await db.log_search_query(
            query_text=request.query,
            results_count=len(result['sources']),
            response_time_ms=result['response_time_ms']
        )
        
        logger.info(f"AI answer with structured extraction: query='{request.query}', data_type={result.get('data_type', 'none')}")
        return result
        
    except Exception as e:
        logger.error(f"AI answer structured error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

