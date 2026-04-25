"""
AskDataSage AI — Query Executor
Executes validated SQL queries against the SQLite database and returns Pandas DataFrames.
Includes timeout control, structured schema extraction, and database preview.
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
SQL_TIMEOUT_SECONDS = 10  # Max time for any single query


class QueryTimeoutError(Exception):
    """Raised when a SQL query exceeds the allowed execution time."""
    pass


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
        conn = sqlite3.connect(uri, uri=True, timeout=SQL_TIMEOUT_SECONDS)
        conn.row_factory = sqlite3.Row
        return conn

    def execute(self, sql: str) -> tuple[pd.DataFrame | None, str | None]:
        """Execute SQL and return (dataframe, error_message). Enforces timeout."""
        start_time = time.time()
        conn = None
        try:
            conn = self._get_connection()

            # Set a progress handler to check timeout during query execution
            # The handler is called every N SQLite VM instructions
            def _timeout_check():
                if time.time() - start_time > SQL_TIMEOUT_SECONDS:
                    return 1  # non-zero cancels the query
                return 0

            conn.set_progress_handler(_timeout_check, 1000)

            df = pd.read_sql_query(sql, conn)
            elapsed = round(time.time() - start_time, 3)

            if len(df) > MAX_ROWS:
                logger.warning(f"Truncating {len(df)} rows to {MAX_ROWS}")
                df = df.head(MAX_ROWS)

            logger.info(f"Query OK: {len(df)} rows in {elapsed}s | {sql[:80]}")
            return df, None

        except sqlite3.OperationalError as e:
            elapsed = round(time.time() - start_time, 3)
            if elapsed >= SQL_TIMEOUT_SECONDS or "interrupted" in str(e).lower():
                error_msg = (
                    f"Query timed out after {SQL_TIMEOUT_SECONDS}s. "
                    "Try simplifying your question or adding filters."
                )
                logger.error(f"Query timeout: {sql[:100]}")
            else:
                error_msg = f"SQL error: {str(e)}"
                logger.error(f"{error_msg} | {sql[:100]}")
            return None, error_msg

        except (sqlite3.Error, pd.errors.DatabaseError) as e:
            error_msg = f"SQL error: {str(e)}"
            logger.error(f"{error_msg} | {sql[:100]}")
            return None, error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"{error_msg} | {sql[:100]}")
            return None, error_msg

        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

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

    def get_structured_schema(self) -> list[dict]:
        """
        Return structured schema: list of tables with columns, types, and row counts.
        Used for richer LLM prompts and sidebar data preview.
        """
        tables = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get table names (exclude SQLite internal tables)
            cursor.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                "ORDER BY name"
            )
            table_names = [row[0] for row in cursor.fetchall()]

            for table_name in table_names:
                # Get column info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [
                    {"name": row[1], "type": row[2], "nullable": not row[3]}
                    for row in cursor.fetchall()
                ]

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]

                # Get sample values for key columns (first 3 rows)
                df_sample = pd.read_sql_query(
                    f"SELECT * FROM {table_name} LIMIT 3", conn
                )

                tables.append({
                    "name": table_name,
                    "columns": columns,
                    "row_count": row_count,
                    "sample": df_sample,
                })

            conn.close()
            logger.info(f"Structured schema loaded: {len(tables)} tables")
            return tables

        except Exception as e:
            logger.error(f"Failed to get structured schema: {e}")
            return []

    def get_schema_for_llm(self) -> str:
        """
        Return a richly formatted schema string optimized for LLM consumption.
        Includes table names, columns with types, row counts, and sample data.
        """
        tables = self.get_structured_schema()
        if not tables:
            return self.get_schema()  # fallback to raw CREATE TABLE

        parts = []
        for table in tables:
            cols_desc = ", ".join(
                f"{c['name']} ({c['type']})" for c in table["columns"]
            )
            part = (
                f"TABLE: {table['name']} ({table['row_count']:,} rows)\n"
                f"  COLUMNS: {cols_desc}\n"
                f"  SAMPLE DATA:\n{table['sample'].to_string(index=False)}"
            )
            parts.append(part)

        return "\n\n".join(parts)

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
