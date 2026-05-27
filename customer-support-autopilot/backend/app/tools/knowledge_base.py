"""
Knowledge base management tools.

Handles loading and managing FAQ documents.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any

from app.core.rag_engine import init_rag_engine

logger = logging.getLogger(__name__)


async def reload_knowledge_base() -> Dict[str, Any]:
    """
    Reload the knowledge base from markdown files.
    
    Returns:
        Result with number of chunks indexed
    """
    try:
        # Reinitialize RAG engine
        await init_rag_engine()
        
        return {
            "status": "success",
            "message": "Knowledge base reloaded successfully",
        }
    except Exception as e:
        logger.error(f"Error reloading knowledge base: {e}")
        return {
            "status": "error",
            "message": str(e),
        }


def list_kb_files() -> List[Dict[str, Any]]:
    """
    List all knowledge base files.
    
    Returns:
        List of file information dictionaries
    """
    kb_dir = Path("/app/knowledge_base")
    
    if not kb_dir.exists():
        return []
    
    files = []
    for file_path in kb_dir.glob("*.md"):
        try:
            stat = file_path.stat()
            files.append({
                "name": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })
        except Exception as e:
            logger.error(f"Error reading file info: {e}")
    
    return files
