"""
Real text embeddings using sentence-transformers.

Provides semantic embeddings for RAG knowledge base retrieval.
"""
import logging
from typing import List

logger = logging.getLogger(__name__)

# Try to import sentence-transformers, fall back to simple embedding if not available
try:
    from sentence_transformers import SentenceTransformer
    
    # Global model instance (lazy loading)
    _model = None
    
    def get_model() -> SentenceTransformer:
        """Get or load the sentence transformer model."""
        global _model
        if _model is None:
            logger.info("Loading sentence-transformer model (all-MiniLM-L6-v2)...")
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Model loaded successfully")
        return _model
    
    async def embed_text(text: str) -> List[float]:
        """
        Generate real semantic embeddings for text using sentence-transformers.
        
        Args:
            text: Text to embed
            
        Returns:
            384-dimensional embedding vector
        """
        try:
            model = get_model()
            embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding with sentence-transformers: {e}")
            # Fallback to simple embedding
            return _fallback_embedding(text)
            
except ImportError:
    logger.warning("sentence-transformers not installed, using fallback embedding")
    
    async def embed_text(text: str) -> List[float]:
        """Fallback embedding when sentence-transformers is not available."""
        return _fallback_embedding(text)


def _fallback_embedding(text: str) -> List[float]:
    """
    Simple fallback embedding using word frequency and character hashing.
    
    This produces 384-dimensional vectors that are better than pure hash-based
    approaches, though not as semantically meaningful as ML embeddings.
    
    Args:
        text: Text to embed
        
    Returns:
        384-dimensional embedding vector
    """
    # Initialize zero vector
    embedding = [0.0] * 384
    
    # Simple tokenization
    words = text.lower().split()
    
    if not words:
        return embedding
    
    # Hash each word to multiple dimensions
    for i, word in enumerate(words):
        for j, char in enumerate(word[:20]):  # Limit to first 20 chars per word
            dim = (hash(char) + i * 7 + j * 13) % 384
            embedding[dim] += 1.0 / len(words)
    
    # Add length feature
    embedding[len(words) % 384] += min(len(words), 100) / 100.0
    
    # Normalize to unit vector
    magnitude = sum(x * x for x in embedding) ** 0.5
    if magnitude > 0:
        embedding = [x / magnitude for x in embedding]
    
    return embedding
