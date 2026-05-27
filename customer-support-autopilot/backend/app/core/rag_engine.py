"""
RAG (Retrieval-Augmented Generation) engine for knowledge base.

Handles loading, chunking, embedding, and retrieving FAQ documents.
"""
import hashlib
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import get_settings
from app.integrations.vector_db import get_vector_client, embed_text
from app.integrations.embeddings import embed_text as semantic_embed_text

# Use semantic embeddings when available
embed_text = semantic_embed_text

logger = logging.getLogger(__name__)
settings = get_settings()

# Constants
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
KB_DIRECTORY = Path("/app/knowledge_base")


class RAGEngine:
    """RAG engine for knowledge base retrieval."""
    
    def __init__(self):
        self.vector_client = None
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the RAG engine."""
        try:
            self.vector_client = await get_vector_client()
            self.initialized = True
            logger.info("RAG engine initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize RAG engine: {e}")
            self.initialized = False
    
    def _load_markdown_files(self) -> List[Dict[str, str]]:
        """Load all markdown files from the knowledge base directory."""
        documents = []
        
        if not KB_DIRECTORY.exists():
            logger.warning(f"Knowledge base directory not found: {KB_DIRECTORY}")
            return documents
        
        for file_path in KB_DIRECTORY.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                documents.append({
                    "source": file_path.name,
                    "content": content,
                    "path": str(file_path),
                })
                logger.info(f"Loaded knowledge base file: {file_path.name}")
            except Exception as e:
                logger.error(f"Error loading file {file_path}: {e}")
        
        return documents
    
    def _chunk_text(self, text: str, source: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks."""
        chunks = []
        
        # Simple character-based chunking
        # In production, use semantic chunking or token-based chunking
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk_text = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind(".")
                last_newline = chunk_text.rfind("\n")
                break_point = max(last_period, last_newline)
                
                if break_point > CHUNK_SIZE // 2:
                    end = start + break_point + 1
                    chunk_text = text[start:end]
            
            # Create chunk
            chunk_id = hashlib.md5(
                f"{source}:{chunk_index}:{chunk_text[:50]}".encode()
            ).hexdigest()
            
            chunks.append({
                "id": chunk_id,
                "text": chunk_text.strip(),
                "source": source,
                "chunk_index": chunk_index,
                "start_char": start,
                "end_char": end,
            })
            
            # Move to next chunk with overlap
            start = end - CHUNK_OVERLAP
            chunk_index += 1
        
        return chunks
    
    async def load_knowledge_base(self) -> int:
        """
        Load and index all knowledge base documents.
        
        Returns:
            Number of chunks indexed
        """
        if not self.initialized:
            await self.initialize()
        
        if not self.vector_client:
            logger.warning("Vector client not available, skipping knowledge base loading")
            return 0
        
        documents = self._load_markdown_files()
        total_chunks = 0
        
        for doc in documents:
            chunks = self._chunk_text(doc["content"], doc["source"])
            
            for chunk in chunks:
                try:
                    # Generate embedding
                    embedding = await embed_text(chunk["text"])
                    
                    # Prepare payload
                    payload = {
                        "text": chunk["text"],
                        "source": chunk["source"],
                        "chunk_index": chunk["chunk_index"],
                    }
                    
                    # Upsert to vector DB
                    await self.vector_client.upsert(
                        vector_id=chunk["id"],
                        vector=embedding,
                        payload=payload,
                    )
                    
                    total_chunks += 1
                except Exception as e:
                    logger.error(f"Error indexing chunk: {e}")
        
        logger.info(f"Indexed {total_chunks} chunks from {len(documents)} documents")
        return total_chunks
    
    async def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with scores
        """
        if not self.initialized or not self.vector_client:
            return []
        
        try:
            # Generate query embedding
            query_embedding = await embed_text(query)
            
            # Search vector DB
            results = await self.vector_client.search(
                vector=query_embedding,
                limit=top_k,
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "text": result.payload.get("text", ""),
                    "source": result.payload.get("source", ""),
                    "score": result.score,
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error retrieving knowledge: {e}")
            return []


# Global RAG engine instance
rag_engine = RAGEngine()


async def retrieve_knowledge(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieve relevant knowledge base chunks.
    
    Convenience function using the global RAG engine.
    """
    return await rag_engine.retrieve(query, top_k)


async def init_rag_engine() -> None:
    """Initialize the global RAG engine."""
    await rag_engine.initialize()
    await rag_engine.load_knowledge_base()
