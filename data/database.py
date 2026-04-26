"""
Database Initialization Module
Handles robust connection management and automatic demo data seeding.
"""

import os
import sqlite3
import streamlit as st
from pathlib import Path

from src.logger import get_logger
import data.generate_data as gd

logger = get_logger("database")

# Robust path handling
BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "ecommerce.db"


def seed_demo_data(db_path: Path):
    """Seed demo data if database is empty or missing."""
    logger.info(f"Seeding demo data to {db_path}...")
    try:
        # Override the DB_PATH in generate_data module so it writes to our robust path
        gd.DB_PATH = str(db_path)
        gd.generate_database()
        logger.info("Demo data seeding complete.")
    except Exception as e:
        logger.error(f"Failed to seed demo data: {e}")
        raise

@st.cache_resource(show_spinner=False)
def init_database(db_path: str = str(DB_PATH)) -> str:
    """
    Initialize the database, creating it if it doesn't exist.
    Cached to run only once per Streamlit server lifecycle.
    """
    path_obj = Path(db_path)
    
    # Ensure data directory exists
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Checking database at: {path_obj}")
    
    if not path_obj.exists():
        logger.warning(f"Database not found at {path_obj}. Initializing...")
        seed_demo_data(path_obj)
    else:
        # Also check if it's an empty file (e.g. from touch or failed prior generation)
        if path_obj.stat().st_size == 0:
            logger.warning("Database file is empty. Initializing...")
            seed_demo_data(path_obj)
        else:
            logger.info("Database verified and ready.")
            
    return str(path_obj)

def get_connection(db_path: str = str(DB_PATH)) -> sqlite3.Connection:
    """
    Get a connection to the database.
    (Note: we don't cache this object across all sessions directly because 
    sqlite connection threading might behave unexpectedly with custom row_factories 
    and progress handlers if used concurrently).
    """
    # Ensure database is initialized before getting connection
    init_database(db_path)
    
    uri = f"file:{db_path}?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=10, check_same_thread=False)

def get_debug_info() -> dict:
    """Return debugging information about the environment."""
    return {
        "cwd": os.getcwd(),
        "base_dir": str(BASE_DIR),
        "data_dir": str(DATA_DIR),
        "db_path": str(DB_PATH),
        "db_exists": DB_PATH.exists(),
        "db_size_bytes": DB_PATH.stat().st_size if DB_PATH.exists() else 0,
        "files_in_data": [f.name for f in DATA_DIR.iterdir() if f.is_file()] if DATA_DIR.exists() else []
    }
