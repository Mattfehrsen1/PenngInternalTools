import os
from typing import List, Optional
import openai
from openai import AsyncOpenAI
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Global client to reuse connections
_openai_client = None

@asynccontextmanager
async def get_openai_client():
    """Get a shared OpenAI client with proper lifecycle management"""
    global _openai_client
    
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        _openai_client = AsyncOpenAI(api_key=api_key)
    
    try:
        yield _openai_client
    except Exception as e:
        logger.error(f"Error with OpenAI client: {e}")
        raise

class Embedder:
    def __init__(self):
        self.model = "text-embedding-3-small"
        self.batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))
        self.max_retries = 3
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts"""
        try:
            async with get_openai_client() as client:
                response = await client.embeddings.create(
                    model=self.model,
                    input=texts
                )
                return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            raise
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents in batches
        
        Args:
            texts: List of text documents to embed
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        all_embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        logger.info(f"Embedding {len(texts)} texts in {total_batches} batches")
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            try:
                logger.debug(f"Processing batch {batch_num}/{total_batches}")
                embeddings = await self._embed_batch(batch)
                all_embeddings.extend(embeddings)
                
                # Small delay to avoid rate limits
                if batch_num < total_batches:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Failed to embed batch {batch_num}: {e}")
                # Return partial results if some batches succeeded
                if all_embeddings:
                    logger.warning(f"Returning {len(all_embeddings)} embeddings out of {len(texts)} requested")
                    return all_embeddings
                raise
        
        logger.info(f"Successfully embedded {len(all_embeddings)} texts")
        return all_embeddings
    
    async def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query text
        
        Args:
            query: Query text to embed
        
        Returns:
            Embedding vector
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            async with get_openai_client() as client:
                response = await client.embeddings.create(
                    model=self.model,
                    input=query
                )
                return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise
    
    def estimate_cost(self, text_count: int, avg_tokens_per_text: int = 100) -> float:
        """
        Estimate embedding cost in USD
        
        Args:
            text_count: Number of texts to embed
            avg_tokens_per_text: Average tokens per text (estimate)
        
        Returns:
            Estimated cost in USD
        """
        # Pricing for text-embedding-3-small as of 2024
        # $0.00002 per 1K tokens
        price_per_1k_tokens = 0.00002
        
        total_tokens = text_count * avg_tokens_per_text
        cost = (total_tokens / 1000) * price_per_1k_tokens
        
        return round(cost, 6)
