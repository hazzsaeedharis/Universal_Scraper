"""
RAG retriever for semantic search with re-ranking and source attribution.
"""
from typing import List, Dict, Optional
import time

from .embedder import Embedder
from .vector_store import VectorStore
from ..config import get_settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class Retriever:
    """RAG retriever for semantic search."""
    
    def __init__(self):
        """Initialize the retriever."""
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        
        settings = get_settings()
        self.top_k = settings.top_k_results
    
    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        namespace: str = "",
        filter: Optional[Dict] = None
    ) -> Dict:
        """
        Perform semantic search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            namespace: Namespace to search
            filter: Optional metadata filter
            
        Returns:
            Dictionary with results and metadata
        """
        start_time = time.time()
        
        # Embed the query
        logger.info(f"Searching for: {query}")
        query_vector = self.embedder.embed_text(query)
        
        # Query vector store
        k = top_k or self.top_k
        results = self.vector_store.query(
            vector=query_vector,
            top_k=k,
            namespace=namespace,
            filter=filter,
            include_metadata=True
        )
        
        # Format results with source attribution
        formatted_results = []
        for result in results:
            metadata = result.get('metadata', {})
            formatted_results.append({
                "text": metadata.get('text', ''),
                "score": result['score'],
                "source": {
                    "url": metadata.get('url', ''),
                    "title": metadata.get('title', ''),
                    "domain": metadata.get('domain', ''),
                    "chunk_index": metadata.get('chunk_index', 0)
                },
                "id": result['id']
            })
        
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "query": query,
            "results": formatted_results,
            "count": len(formatted_results),
            "response_time_ms": response_time
        }
    
    def get_context_window(
        self,
        results: List[Dict],
        max_tokens: int = 4000
    ) -> str:
        """
        Create a context window from search results.
        
        Args:
            results: Search results
            max_tokens: Maximum tokens (approximate as words * 1.3)
            
        Returns:
            Concatenated context string
        """
        context_parts = []
        total_words = 0
        max_words = int(max_tokens / 1.3)
        
        for result in results:
            text = result.get('text', '')
            words = len(text.split())
            
            if total_words + words > max_words:
                break
            
            source = result.get('source', {})
            context_parts.append(
                f"[Source: {source.get('title', 'Unknown')} - {source.get('url', '')}]\n{text}\n"
            )
            total_words += words
        
        return "\n---\n".join(context_parts)
    
    def rerank_results(
        self,
        query: str,
        results: List[Dict]
    ) -> List[Dict]:
        """
        Re-rank results based on query similarity.
        Simple implementation - can be enhanced with cross-encoder.
        
        Args:
            query: Original query
            results: Initial results
            
        Returns:
            Re-ranked results
        """
        # Embed query
        query_embedding = self.embedder.embed_text(query)
        
        # Calculate new scores
        for result in results:
            text = result.get('text', '')
            if text:
                text_embedding = self.embedder.embed_text(text)
                similarity = self.embedder.similarity(query_embedding, text_embedding)
                result['rerank_score'] = similarity
        
        # Sort by new scores
        results.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
        
        return results

