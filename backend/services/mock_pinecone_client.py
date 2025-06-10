"""Mock Pinecone client for testing without valid API key"""
import logging
from typing import List, Dict, Optional, Tuple
import uuid
import json
import os

logger = logging.getLogger(__name__)

class MockPineconeClient:
    """Mock implementation of PineconeClient for testing"""
    
    def __init__(self):
        logger.warning("Using MockPineconeClient - no actual Pinecone operations will be performed")
        self.index_name = "clone-advisor"
        # Store vectors in memory for this session
        self._vectors = {}
        # Also persist to a file for debugging
        self._storage_file = "mock_pinecone_data.json"
        self._load_data()
    
    def _load_data(self):
        """Load persisted mock data"""
        if os.path.exists(self._storage_file):
            try:
                with open(self._storage_file, 'r') as f:
                    self._vectors = json.load(f)
                logger.info(f"Loaded {len(self._vectors)} vectors from mock storage")
            except:
                self._vectors = {}
    
    def _save_data(self):
        """Save mock data to file"""
        try:
            with open(self._storage_file, 'w') as f:
                json.dump(self._vectors, f)
        except Exception as e:
            logger.error(f"Error saving mock data: {e}")
    
    async def upsert_vectors(
        self,
        namespace: str,
        embeddings: List[List[float]],
        metadata: List[Dict],
        ids: Optional[List[str]] = None
    ) -> Dict:
        """Mock upsert operation"""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(embeddings))]
        
        # Store in namespace
        if namespace not in self._vectors:
            self._vectors[namespace] = {}
        
        upserted_count = 0
        for i, (vector_id, embedding, meta) in enumerate(zip(ids, embeddings, metadata)):
            self._vectors[namespace][vector_id] = {
                "values": embedding[:10],  # Store only first 10 values to save space
                "metadata": meta
            }
            upserted_count += 1
        
        self._save_data()
        logger.info(f"Mock upserted {upserted_count} vectors to namespace {namespace}")
        
        return {
            "upserted_count": upserted_count,
            "namespace": namespace
        }
    
    async def similarity_search(
        self,
        namespace: str,
        query_vector: List[float],
        k: int = 10,
        filter: Optional[Dict] = None
    ) -> List[Tuple[str, float, Dict]]:
        """Mock similarity search - returns all vectors in namespace"""
        if namespace not in self._vectors:
            return []
        
        # For mock, just return the first k vectors
        results = []
        for vector_id, data in list(self._vectors[namespace].items())[:k]:
            # Mock similarity score
            score = 0.95
            results.append((vector_id, score, data["metadata"]))
        
        logger.info(f"Mock search in {namespace} returned {len(results)} results")
        return results
    
    async def delete_namespace(self, namespace: str) -> bool:
        """Mock delete namespace"""
        if namespace in self._vectors:
            del self._vectors[namespace]
            self._save_data()
            logger.info(f"Mock deleted namespace {namespace}")
            return True
        return False

    async def check_namespace_exists(self, namespace: str) -> Tuple[bool, int]:
        """
        Check if a namespace exists and return vector count
        
        Args:
            namespace: Namespace to check
        
        Returns:
            Tuple of (exists: bool, vector_count: int)
        """
        if namespace in self._vectors:
            vector_count = len(self._vectors[namespace])
            logger.info(f"Mock namespace {namespace} exists with {vector_count} vectors")
            return True, vector_count
        else:
            logger.info(f"Mock namespace {namespace} does not exist")
            return False, 0
