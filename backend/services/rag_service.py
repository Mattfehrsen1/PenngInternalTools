import logging
from typing import List, Dict, Any
from services.pinecone_client import get_pinecone_client
from services.embedder import Embedder

logger = logging.getLogger(__name__)

class RAGService:
    """
    Service for querying the RAG system from ElevenLabs function calls
    Provides a simple interface to the existing Pinecone + Embedder infrastructure
    """
    
    def __init__(self):
        self.pinecone_client = get_pinecone_client()
        self.embedder = Embedder()
    
    async def query_documents(
        self, 
        query: str, 
        namespace: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query documents in the specified namespace
        
        Args:
            query: The user's question
            namespace: Persona's Pinecone namespace
            top_k: Number of relevant chunks to return
            
        Returns:
            List of relevant document chunks with text and metadata
        """
        try:
            # Check if namespace exists and has vectors
            exists, vector_count = await self.pinecone_client.check_namespace_exists(namespace)
            
            if not exists or vector_count == 0:
                logger.warning(f"Namespace {namespace} does not exist or is empty")
                return []
            
            # Embed the query
            query_embedding = await self.embedder.embed_query(query)
            
            # Search for relevant chunks
            chunks = await self.pinecone_client.similarity_search(
                namespace=namespace,
                query_embedding=query_embedding,
                k=top_k
            )
            
            # Format results for ElevenLabs function calls
            formatted_results = []
            for chunk in chunks:
                metadata = chunk.get("metadata", {})
                formatted_results.append({
                    "text": metadata.get("text", ""),
                    "source": metadata.get("source", "Unknown"),
                    "page": metadata.get("page", 1),
                    "score": chunk.get("score", 0.0),
                    "source_type": metadata.get("source_type", "document")
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying documents in namespace {namespace}: {str(e)}")
            return [] 