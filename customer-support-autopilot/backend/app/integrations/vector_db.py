"""
Vector database client for Qdrant.

Handles vector storage and similarity search.
"""
import logging
from typing import List, Optional, Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Constants
COLLECTION_NAME = "csa_kb"
VECTOR_SIZE = 384  # Compatible with common embedding models


class VectorDBClient:
    """Qdrant vector database client."""
    
    def __init__(self):
        self.client = None
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize Qdrant client."""
        try:
            # Initialize Qdrant client
            self.client = QdrantClient(url=settings.qdrant_url)
            
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if COLLECTION_NAME not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")
            else:
                logger.info(f"Qdrant collection exists: {COLLECTION_NAME}")
            
            self.initialized = True
            
        except Exception as e:
            logger.warning(f"Failed to initialize Qdrant: {e}")
            self.initialized = False
    
    async def upsert(
        self,
        vector_id: str,
        vector: List[float],
        payload: dict,
    ) -> bool:
        """
        Upsert a vector into the database.
        
        Args:
            vector_id: Unique identifier for the vector
            vector: Embedding vector
            payload: Metadata to store with the vector
            
        Returns:
            True if successful
        """
        if not self.initialized or not self.client:
            return False
        
        try:
            point = PointStruct(
                id=vector_id,
                vector=vector,
                payload=payload,
            )
            
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[point],
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting vector: {e}")
            return False
    
    async def search(
        self,
        vector: List[float],
        limit: int = 5,
    ) -> List[Any]:
        """
        Search for similar vectors.
        
        Args:
            vector: Query embedding
            limit: Number of results to return
            
        Returns:
            List of search results with scores
        """
        if not self.initialized or not self.client:
            return []
        
        try:
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=vector,
                limit=limit,
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []


# Global vector DB client
vector_db_client = VectorDBClient()


async def get_vector_client() -> VectorDBClient:
    """Get initialized vector database client."""
    if not vector_db_client.initialized:
        await vector_db_client.initialize()
    return vector_db_client


async def init_vector_db() -> None:
    """Initialize the vector database."""
    await vector_db_client.initialize()
