#!/usr/bin/env python3
"""
Run database migrations for escalations and token usage tables.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("/app/data/escalations.db")


def run_migrations():
    """Create database tables."""
    # Ensure directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create escalations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            intent TEXT,
            message TEXT NOT NULL,
            conversation_history TEXT,
            sentiment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            resolved_at TIMESTAMP,
            notes TEXT
        )
    """)
    
    # Create token_usage table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            tokens_used INTEGER,
            endpoint TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("Database migrations completed successfully")


if __name__ == "__main__":
    run_migrations()
