"""
RAG service combining retrieval and generation for AI-powered answers.
"""
from typing import Dict, Optional
import time

from .retriever import Retriever
from ..ai.groq_client import GroqClient
from ..ai.structured_extractor import StructuredExtractor
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class RAGService:
    """RAG service for generating AI answers from retrieved context."""
    
    def __init__(self):
        """Initialize RAG service."""
        self.retriever = Retriever()
        self.groq_client = GroqClient(model="llama-3.3-70b-versatile")
        self.extractor = StructuredExtractor()
        logger.info("RAG service initialized")
    
    async def answer_query(
        self,
        query: str,
        top_k: int = 5,
        namespace: str = "",
        filter: Optional[Dict] = None,
        extract_structured: bool = False
    ) -> Dict:
        """
        Generate an AI answer for a query using RAG.
        
        Args:
            query: User's question
            top_k: Number of chunks to retrieve
            namespace: Namespace to search
            filter: Optional metadata filter
            extract_structured: Whether to extract structured data
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        start_time = time.time()
        logger.info(f"RAG query: '{query}' (top_k={top_k}, namespace={namespace})")
        
        # Step 1: Retrieve relevant chunks
        search_results = await self.retriever.search(
            query=query,
            top_k=top_k,
            namespace=namespace,
            filter=filter
        )
        
        if not search_results['results']:
            logger.warning(f"No results found for query: {query}")
            return {
                "query": query,
                "answer": "I couldn't find any relevant information in the scraped content to answer your question. Please make sure you've scraped content related to this topic.",
                "sources": [],
                "search_results": search_results['results'],
                "response_time_ms": (time.time() - start_time) * 1000
            }
        
        # Step 2: Prepare context from retrieved chunks
        context_parts = []
        for i, result in enumerate(search_results['results'], 1):
            source_info = f"[Source {i}: {result['source']['title']} - {result['source']['url']}]"
            context_parts.append(f"{source_info}\n{result['text']}\n")
        
        context = "\n---\n".join(context_parts)
        
        # Step 3: Generate answer using Groq
        system_prompt = """You are a helpful AI assistant that answers questions based on provided context.

Your task:
1. Read the context from multiple sources carefully
2. Answer the user's question directly and concisely
3. Use information ONLY from the provided context
4. If the context doesn't contain enough information, say so
5. Cite source numbers when referencing specific information (e.g., "According to Source 1...")
6. Be conversational and natural in your response

Remember: Only use information from the provided context. Do not make up information."""

        user_prompt = f"""Context from scraped web pages:

{context}

---

User Question: {query}

Please provide a clear, concise answer based on the context above."""

        try:
            answer = self.groq_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1024
            )
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            answer = "I encountered an error while generating the answer. Please try again."
        
        # Step 4: Prepare sources list
        sources = []
        for result in search_results['results']:
            sources.append({
                "title": result['source']['title'],
                "url": result['source']['url'],
                "domain": result['source']['domain'],
                "score": result['score']
            })
        
        response_time = (time.time() - start_time) * 1000
        logger.info(f"RAG query completed in {response_time:.0f}ms, {len(sources)} sources")
        
        result = {
            "query": query,
            "answer": answer,
            "sources": sources,
            "search_results": search_results['results'],
            "response_time_ms": response_time
        }
        
        # Step 5: Extract structured data if requested
        if extract_structured:
            extraction_result = self.extractor.extract(query, answer, context)
            result.update({
                "data_type": extraction_result["data_type"],
                "confidence": extraction_result["confidence"],
                "structured_data": extraction_result["structured_data"],
                "has_structured_data": extraction_result["has_structured_data"]
            })
            logger.info(f"Structured extraction: type={extraction_result['data_type']}, success={extraction_result['has_structured_data']}")
        
        return result


