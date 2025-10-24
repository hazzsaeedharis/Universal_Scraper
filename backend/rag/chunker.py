"""
Text chunking with overlap for context preservation.
"""
from typing import List, Dict
from ..config import get_settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class Chunker:
    """Text chunker with overlap."""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks
        """
        settings = get_settings()
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
    
    def chunk_text(
        self,
        text: str,
        metadata: Dict = None
    ) -> List[Dict]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries
        """
        if not text:
            return []
        
        # Split by sentences for better boundaries
        sentences = self._split_sentences(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # If adding this sentence exceeds chunk size
            if current_size + sentence_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(self._create_chunk(chunk_text, len(chunks), metadata))
                
                # Start new chunk with overlap
                overlap_text = chunk_text[-self.chunk_overlap:] if len(chunk_text) > self.chunk_overlap else chunk_text
                current_chunk = [overlap_text, sentence]
                current_size = len(overlap_text) + sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(self._create_chunk(chunk_text, len(chunks), metadata))
        
        logger.info(f"Created {len(chunks)} chunks from text of length {len(text)}")
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        Simple implementation - can be enhanced with NLTK.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting by common punctuation
        import re
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _create_chunk(
        self,
        text: str,
        index: int,
        metadata: Dict = None
    ) -> Dict:
        """
        Create a chunk dictionary.
        
        Args:
            text: Chunk text
            index: Chunk index
            metadata: Optional metadata
            
        Returns:
            Chunk dictionary
        """
        chunk = {
            "text": text,
            "index": index,
            "char_count": len(text),
            "word_count": len(text.split())
        }
        
        if metadata:
            chunk["metadata"] = metadata
        
        return chunk
    
    def chunk_documents(
        self,
        documents: List[Dict]
    ) -> List[Dict]:
        """
        Chunk multiple documents.
        
        Args:
            documents: List of document dictionaries with 'text' and optional 'metadata'
            
        Returns:
            List of chunks with source document metadata
        """
        all_chunks = []
        
        for doc_idx, doc in enumerate(documents):
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            
            # Add document index to metadata
            metadata['doc_index'] = doc_idx
            
            # Chunk the document
            chunks = self.chunk_text(text, metadata)
            all_chunks.extend(chunks)
        
        return all_chunks

