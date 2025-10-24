"""
Pinecone vector store wrapper for upserting and querying vectors.
"""
from typing import List, Dict, Optional
from pinecone import Pinecone, ServerlessSpec
import time

from ..config import get_settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class VectorStore:
    """Pinecone vector store manager."""
    
    def __init__(self):
        """Initialize the Pinecone client."""
        settings = get_settings()
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.index = None
        
        logger.info(f"Pinecone client initialized for index: {self.index_name}")
    
    def create_index(
        self,
        dimension: int,
        metric: str = "cosine",
        cloud: str = "aws",
        region: str = "us-east-1"
    ):
        """
        Create a Pinecone index if it doesn't exist.
        
        Args:
            dimension: Embedding dimension
            metric: Distance metric (cosine, euclidean, dotproduct)
            cloud: Cloud provider
            region: Cloud region
        """
        # Check if index exists
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        
        if self.index_name in existing_indexes:
            logger.info(f"Index {self.index_name} already exists")
        else:
            logger.info(f"Creating index {self.index_name} with dimension {dimension}")
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(
                    cloud=cloud,
                    region=region
                )
            )
            
            # Wait for index to be ready
            while not self.pc.describe_index(self.index_name).status['ready']:
                time.sleep(1)
            
            logger.info(f"Index {self.index_name} created successfully")
        
        # Connect to index
        self.index = self.pc.Index(self.index_name)
    
    def connect(self):
        """Connect to existing index."""
        if not self.index:
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to index: {self.index_name}")
    
    def upsert_vectors(
        self,
        vectors: List[tuple],
        namespace: str = ""
    ) -> dict:
        """
        Upsert vectors to Pinecone.
        
        Args:
            vectors: List of tuples (id, embedding, metadata)
            namespace: Optional namespace for organization
            
        Returns:
            Upsert response
        """
        if not self.index:
            self.connect()
        
        logger.info(f"Upserting {len(vectors)} vectors to namespace '{namespace}'")
        
        # Batch upsert (Pinecone recommends batches of 100)
        batch_size = 100
        responses = []
        
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            response = self.index.upsert(
                vectors=batch,
                namespace=namespace
            )
            responses.append(response)
        
        total_upserted = sum(r.upserted_count for r in responses)
        logger.info(f"Successfully upserted {total_upserted} vectors")
        
        return {"upserted_count": total_upserted}
    
    def query(
        self,
        vector: List[float],
        top_k: int = 10,
        namespace: str = "",
        filter: Optional[Dict] = None,
        include_metadata: bool = True
    ) -> List[Dict]:
        """
        Query vectors from Pinecone.
        
        Args:
            vector: Query vector
            top_k: Number of results to return
            namespace: Namespace to query
            filter: Optional metadata filter
            include_metadata: Whether to include metadata
            
        Returns:
            List of matching results with scores and metadata
        """
        if not self.index:
            self.connect()
        
        response = self.index.query(
            vector=vector,
            top_k=top_k,
            namespace=namespace,
            filter=filter,
            include_metadata=include_metadata,
            include_values=False
        )
        
        # Format results
        results = []
        for match in response.matches:
            result = {
                "id": match.id,
                "score": match.score,
            }
            if include_metadata and hasattr(match, 'metadata'):
                result["metadata"] = match.metadata
            results.append(result)
        
        logger.info(f"Query returned {len(results)} results")
        return results
    
    def delete(
        self,
        ids: Optional[List[str]] = None,
        namespace: str = "",
        delete_all: bool = False
    ):
        """
        Delete vectors from Pinecone.
        
        Args:
            ids: List of vector IDs to delete
            namespace: Namespace to delete from
            delete_all: Delete all vectors in namespace
        """
        if not self.index:
            self.connect()
        
        if delete_all:
            self.index.delete(delete_all=True, namespace=namespace)
            logger.info(f"Deleted all vectors from namespace '{namespace}'")
        elif ids:
            self.index.delete(ids=ids, namespace=namespace)
            logger.info(f"Deleted {len(ids)} vectors from namespace '{namespace}'")
    
    def get_stats(self) -> dict:
        """Get index statistics."""
        if not self.index:
            self.connect()
        
        stats = self.index.describe_index_stats()
        return {
            "total_vector_count": stats.total_vector_count,
            "dimension": stats.dimension,
            "namespaces": dict(stats.namespaces) if stats.namespaces else {}
        }

