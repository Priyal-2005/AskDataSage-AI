"""
AskDataSage AI — Query Executor
Executes validated SQL queries against the SQLite database and returns Pandas DataFrames.
"""

import os
import sqlite3
import time

import pandas as pd

from src.logger import get_logger

logger = get_logger("executor")

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ecommerce.db"
)
MAX_ROWS = 10_000


class QueryExecutor:
    """Executes SQL queries against the SQLite e-commerce database."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(
                f"Database not found at: {db_path}\n"
                "Run `python data/generate_data.py` to create it."
            )

    def _get_connection(self) -> sqlite3.Connection:
        uri = f"file:{self.db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def execute(self, sql: str) -> tuple[pd.DataFrame | None, str | None]:
        """Execute SQL and return (dataframe, error_message)."""
        start_time = time.time()
        try:
            conn = self._get_connection()
            df = pd.read_sql_query(sql, conn)
            conn.close()
            elapsed = round(time.time() - start_time, 3)
            if len(df) > MAX_ROWS:
                df = df.head(MAX_ROWS)
            logger.info(f"Query OK: {len(df)} rows in {elapsed}s | {sql[:80]}")
            return df, None
        except (sqlite3.Error, pd.errors.DatabaseError) as e:
            error_msg = f"SQL error: {str(e)}"
            logger.error(f"{error_msg} | {sql[:100]}")
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"{error_msg} | {sql[:100]}")
            return None, error_msg

    def get_schema(self) -> str:
        """Return CREATE TABLE statements."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name")
            schemas = [row[0] for row in cursor.fetchall() if row[0]]
            conn.close()
            return "\n\n".join(schemas)
        except Exception as e:
            logger.error(f"Failed to read schema: {e}")
            return ""

    def get_table_samples(self, limit: int = 3) -> str:
        """Return sample rows from each table."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            samples = []
            for table in tables:
                df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT {limit}", conn)
                samples.append(f"-- {table}:\n{df.to_string(index=False)}")
            conn.close()
            return "\n\n".join(samples)
        except Exception as e:
            logger.error(f"Failed to get samples: {e}")
            return ""
