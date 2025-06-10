import os
import pinecone
from typing import List, Dict, Optional, Tuple
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class PineconeClient:
    def __init__(self):
        # Initialize Pinecone
        api_key = os.getenv("PINECONE_API_KEY")
        environment = os.getenv("PINECONE_ENV", "us-east-1-aws")
        project_id = os.getenv("PINECONE_PROJECT_ID")
        
        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables")
        
        # Initialize Pinecone with new API
        self.pc = pinecone.Pinecone(api_key=api_key)
        
        # Index name for the clone advisor
        self.index_name = "clone-advisor"
        
        # Check if index exists, create if not
        try:
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to existing Pinecone index: {self.index_name}")
        except Exception as e:
            logger.warning(f"Index {self.index_name} not found, creating...")
            self._create_index()
            self.index = self.pc.Index(self.index_name)
    
    def _create_index(self):
        """Create Pinecone index with appropriate settings"""
        try:
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,  # OpenAI text-embedding-3-small dimension
                metric="cosine",
                spec=pinecone.ServerlessSpec(
                    cloud="aws",
                    region=os.getenv("PINECONE_ENV", "us-east-1")
                )
            )
            logger.info(f"Created new Pinecone index: {self.index_name}")
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def upsert_vectors(
        self,
        namespace: str,
        embeddings: List[List[float]],
        metadata: List[Dict[str, any]],
        ids: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Upsert vectors to Pinecone with metadata
        
        Args:
            namespace: Namespace for the persona (e.g., "persona_uuid")
            embeddings: List of embedding vectors
            metadata: List of metadata dicts corresponding to each embedding
            ids: Optional list of IDs. If not provided, will generate.
        
        Returns:
            Dict with upsert statistics
        """
        if not embeddings:
            return {"upserted_count": 0}
        
        if len(embeddings) != len(metadata):
            raise ValueError("Number of embeddings must match number of metadata entries")
        
        # Generate IDs if not provided
        if ids is None:
            ids = [f"{namespace}_{i}" for i in range(len(embeddings))]
        
        # Prepare vectors for upsert
        vectors = []
        for i, (embedding, meta, vec_id) in enumerate(zip(embeddings, metadata, ids)):
            vectors.append({
                "id": vec_id,
                "values": embedding,
                "metadata": meta
            })
        
        # Upsert in batches
        batch_size = 100
        total_upserted = 0
        
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            try:
                response = self.index.upsert(vectors=batch, namespace=namespace)
                total_upserted += response.upserted_count
            except Exception as e:
                logger.error(f"Error upserting batch {i//batch_size}: {e}")
                raise
        
        logger.info(f"Upserted {total_upserted} vectors to namespace {namespace}")
        return {"upserted_count": total_upserted}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def similarity_search(
        self,
        namespace: str,
        query_embedding: List[float],
        k: int = 6,
        filter: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar vectors in Pinecone
        
        Args:
            namespace: Namespace to search in
            query_embedding: Query vector
            k: Number of results to return
            filter: Optional metadata filter
        
        Returns:
            List of results with scores and metadata
        """
        try:
            response = self.index.query(
                namespace=namespace,
                vector=query_embedding,
                top_k=k,
                include_metadata=True,
                filter=filter
            )
            
            results = []
            for match in response.matches:
                results.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            logger.info(f"Found {len(results)} matches in namespace {namespace}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching in namespace {namespace}: {e}")
            raise
    
    async def check_namespace_exists(self, namespace: str) -> Tuple[bool, int]:
        """
        Check if a namespace exists and return vector count
        
        Args:
            namespace: Namespace to check
        
        Returns:
            Tuple of (exists: bool, vector_count: int)
        """
        try:
            stats = self.index.describe_index_stats()
            namespaces = stats.get('namespaces', {})
            
            if namespace in namespaces:
                vector_count = namespaces[namespace].get('vector_count', 0)
                return True, vector_count
            return False, 0
            
        except Exception as e:
            logger.error(f"Error checking namespace {namespace}: {e}")
            return False, 0
    
    async def delete_namespace(self, namespace: str) -> bool:
        """
        Delete all vectors in a namespace
        
        Args:
            namespace: Namespace to delete
        
        Returns:
            True if successful
        """
        try:
            self.index.delete(delete_all=True, namespace=namespace)
            logger.info(f"Deleted namespace {namespace}")
            return True
        except Exception as e:
            logger.error(f"Error deleting namespace {namespace}: {e}")
            return False

# Singleton instance
_pinecone_client = None

def get_pinecone_client() -> PineconeClient:
    """Get singleton Pinecone client instance"""
    global _pinecone_client
    if _pinecone_client is None:
        try:
            _pinecone_client = PineconeClient()
        except Exception as e:
            logger.error(f"Failed to initialize real Pinecone client: {e}")
            logger.warning("Falling back to MockPineconeClient for testing")
            from .mock_pinecone_client import MockPineconeClient
            _pinecone_client = MockPineconeClient()
    return _pinecone_client
