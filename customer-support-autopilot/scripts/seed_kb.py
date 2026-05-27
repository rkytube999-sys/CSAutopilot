#!/usr/bin/env python3
"""
Seed knowledge base script.

Loads markdown files, chunks them, and indexes in vector database.
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.rag_engine import RAGEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_knowledge_base(kb_file: str):
    """Seed a specific knowledge base file."""
    kb_path = Path(kb_file)
    
    if not kb_path.exists():
        logger.error(f"File not found: {kb_path}")
        return False
    
    # Initialize RAG engine
    rag = RAGEngine()
    await rag.initialize()
    
    if not rag.initialized:
        logger.error("Failed to initialize RAG engine")
        return False
    
    # Load and chunk the file
    documents = rag._load_markdown_files()
    
    if not documents:
        # Try loading the specific file
        content = kb_path.read_text(encoding="utf-8")
        documents = [{
            "source": kb_path.name,
            "content": content,
            "path": str(kb_path),
        }]
    
    total_chunks = 0
    
    for doc in documents:
        chunks = rag._chunk_text(doc["content"], doc["source"])
        
        for chunk in chunks:
            try:
                from app.integrations.groq_client import embed_text
                
                embedding = await embed_text(chunk["text"])
                
                payload = {
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "chunk_index": chunk["chunk_index"],
                }
                
                await rag.vector_client.upsert(
                    vector_id=chunk["id"],
                    vector=embedding,
                    payload=payload,
                )
                
                total_chunks += 1
            except Exception as e:
                logger.error(f"Error indexing chunk: {e}")
    
    logger.info(f"Successfully indexed {total_chunks} chunks")
    return True


def main():
    parser = argparse.ArgumentParser(description="Seed knowledge base into vector DB")
    parser.add_argument("--kb", required=True, help="Path to markdown file or directory")
    args = parser.parse_args()
    
    success = asyncio.run(seed_knowledge_base(args.kb))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
