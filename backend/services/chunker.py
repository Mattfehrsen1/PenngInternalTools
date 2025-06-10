import tiktoken
from typing import List, Dict, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Chunk:
    text: str
    chunk_id: int
    char_start: int
    char_end: int
    token_count: int

class TextChunker:
    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 200,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize text chunker with token-based chunking
        
        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Number of overlapping tokens between chunks
            encoding_name: Tiktoken encoding to use
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
        
        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    def chunk_text(self, text: str, source: str = "document") -> List[Dict]:
        """
        Split text into overlapping chunks based on token count
        
        Args:
            text: Text to chunk
            source: Source identifier for metadata
        
        Returns:
            List of chunk dictionaries with metadata
        """
        if not text or not text.strip():
            return []
        
        # First, split by paragraphs to maintain some semantic coherence
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        current_char_start = 0
        chunk_id = 0
        
        for para_idx, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
            
            para_tokens = self.count_tokens(paragraph)
            
            # If single paragraph is too large, split it
            if para_tokens > self.chunk_size:
                # Split paragraph by sentences or words
                sentences = self._split_paragraph(paragraph)
                
                for sentence in sentences:
                    sent_tokens = self.count_tokens(sentence)
                    
                    if current_tokens + sent_tokens > self.chunk_size and current_chunk:
                        # Save current chunk
                        chunk_text = '\n\n'.join(current_chunk)
                        chunks.append(self._create_chunk_dict(
                            chunk_text,
                            chunk_id,
                            current_char_start,
                            current_char_start + len(chunk_text),
                            source,
                            current_tokens
                        ))
                        
                        # Start new chunk with overlap
                        overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                        current_chunk = [overlap_text] if overlap_text else []
                        current_tokens = self.count_tokens('\n\n'.join(current_chunk)) if current_chunk else 0
                        current_char_start += len(chunk_text) - len(overlap_text) if overlap_text else len(chunk_text)
                        chunk_id += 1
                    
                    current_chunk.append(sentence)
                    current_tokens += sent_tokens
            
            # If adding the paragraph doesn't exceed limit, add it
            elif current_tokens + para_tokens <= self.chunk_size:
                current_chunk.append(paragraph)
                current_tokens += para_tokens
            
            # Otherwise, save current chunk and start new one
            else:
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append(self._create_chunk_dict(
                        chunk_text,
                        chunk_id,
                        current_char_start,
                        current_char_start + len(chunk_text),
                        source,
                        current_tokens
                    ))
                    
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                    current_chunk = [overlap_text] if overlap_text else []
                    current_tokens = self.count_tokens('\n\n'.join(current_chunk)) if current_chunk else 0
                    current_char_start += len(chunk_text) - len(overlap_text) if overlap_text else len(chunk_text)
                    chunk_id += 1
                
                current_chunk.append(paragraph)
                current_tokens = para_tokens
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(self._create_chunk_dict(
                chunk_text,
                chunk_id,
                current_char_start,
                current_char_start + len(chunk_text),
                source,
                current_tokens
            ))
        
        logger.info(f"Created {len(chunks)} chunks from {len(text)} characters")
        return chunks
    
    def _split_paragraph(self, paragraph: str) -> List[str]:
        """Split a paragraph into smaller parts (sentences or phrases)"""
        # Simple sentence splitting - can be improved with NLTK or spaCy
        import re
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        
        result = []
        for sentence in sentences:
            if self.count_tokens(sentence) > self.chunk_size:
                # If even a sentence is too long, split by commas or words
                parts = sentence.split(', ')
                for part in parts:
                    if self.count_tokens(part) <= self.chunk_size:
                        result.append(part)
                    else:
                        # Last resort: split by words
                        words = part.split()
                        current_part = []
                        for word in words:
                            current_part.append(word)
                            if self.count_tokens(' '.join(current_part)) > self.chunk_size * 0.8:
                                result.append(' '.join(current_part))
                                current_part = []
                        if current_part:
                            result.append(' '.join(current_part))
            else:
                result.append(sentence)
        
        return result
    
    def _get_overlap_text(self, chunks: List[str], overlap_tokens: int) -> str:
        """Get text from the end of chunks that contains approximately overlap_tokens"""
        if not chunks:
            return ""
        
        # Start from the last chunk and work backwards
        overlap_text = []
        current_tokens = 0
        
        for chunk in reversed(chunks):
            sentences = chunk.split('. ')
            for sentence in reversed(sentences):
                sent_tokens = self.count_tokens(sentence)
                if current_tokens + sent_tokens <= overlap_tokens:
                    overlap_text.insert(0, sentence)
                    current_tokens += sent_tokens
                else:
                    break
            if current_tokens >= overlap_tokens * 0.8:  # Allow some flexibility
                break
        
        return '. '.join(overlap_text)
    
    def _create_chunk_dict(
        self,
        text: str,
        chunk_id: int,
        char_start: int,
        char_end: int,
        source: str,
        token_count: int
    ) -> Dict:
        """Create a chunk dictionary with metadata"""
        return {
            "text": text,
            "chunk_id": chunk_id,
            "char_start": char_start,
            "char_end": char_end,
            "source": source,
            "token_count": token_count
        }
