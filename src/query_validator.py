"""
AskDataSage AI — Query Validator
Safety layer that ensures only SELECT queries are executed. Blocks dangerous operations.
"""

import re
from src.logger import get_logger

logger = get_logger("validator")

# ---------------------------------------------------------------------------
# Dangerous keywords that must NEVER appear in user-facing queries
# ---------------------------------------------------------------------------
BLOCKED_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
    "TRUNCATE", "EXEC", "EXECUTE", "GRANT", "REVOKE", "MERGE",
    "REPLACE", "ATTACH", "DETACH", "PRAGMA", "VACUUM", "REINDEX",
]

# Regex: match any blocked keyword as a whole word (case-insensitive)
BLOCKED_PATTERN = re.compile(
    r"\b(" + "|".join(BLOCKED_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# Regex: detect comments
COMMENT_PATTERN = re.compile(r"(--|/\*|\*/)")


class QueryValidator:
    """Validates SQL queries for safety before execution."""

    def validate(self, sql: str) -> tuple[bool, str]:
        """
        Validate a SQL query for safety.

        Returns:
            (is_valid, error_message) — error_message is empty string when valid.
        """
        if not sql or not sql.strip():
            logger.warning("Empty SQL query received")
            return False, "Empty query — nothing to execute."

        sql_clean = sql.strip()

        # --- Check for comments (potential injection) ---
        if COMMENT_PATTERN.search(sql_clean):
            logger.warning(f"SQL comments detected: {sql_clean[:100]}")
            return False, "SQL comments are not allowed for security reasons."

        # --- Check for multiple statements (semicolons) ---
        # Remove trailing semicolon (common in generated SQL), then check
        sql_no_trailing = sql_clean.rstrip(";").strip()
        if ";" in sql_no_trailing:
            logger.warning(f"Multiple statements detected: {sql_clean[:100]}")
            return False, "Multiple SQL statements are not allowed. Please use a single query."

        # --- Check for blocked keywords ---
        match = BLOCKED_PATTERN.search(sql_clean)
        if match:
            keyword = match.group(1).upper()
            logger.warning(f"Blocked keyword '{keyword}' found in: {sql_clean[:100]}")
            return False, f"The keyword `{keyword}` is not allowed. Only SELECT queries are permitted."

        # --- Must start with SELECT or WITH (for CTEs) ---
        sql_upper = sql_clean.upper().lstrip()
        if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
            logger.warning(f"Non-SELECT query: {sql_clean[:100]}")
            return False, "Only SELECT queries are allowed. Your query must start with SELECT or WITH."

        # --- If starts with WITH, ensure it contains SELECT ---
        if sql_upper.startswith("WITH") and "SELECT" not in sql_upper:
            logger.warning(f"WITH clause without SELECT: {sql_clean[:100]}")
            return False, "CTE (WITH) queries must contain a SELECT statement."

        logger.info(f"Query validated successfully: {sql_clean[:80]}...")
        return True, ""
