"""
AskDataSage AI — SQL Generator
Converts natural language questions to SQL using Groq LLM with schema-aware prompting.
"""

import os
import re

from groq import Groq
from dotenv import load_dotenv

from src.logger import get_logger

load_dotenv()
logger = get_logger("sql_generator")

# ---------------------------------------------------------------------------
# System prompt with schema and few-shot examples
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an expert SQL query generator for a SQLite e-commerce database.

DATABASE SCHEMA:
{schema}

RULES:
1. Output ONLY the SQL query — no markdown fences, no explanations, no comments.
2. Use only SELECT statements. Never use DROP, DELETE, UPDATE, INSERT, or any DDL.
3. Use proper SQLite syntax (e.g., strftime for dates, || for concatenation).
4. Always use meaningful column aliases with AS.
5. For date filtering, dates are stored as ISO strings ('YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS').
6. Round monetary values to 2 decimal places using ROUND().
7. Limit results to 100 rows unless the user asks for all data.
8. When asked about "revenue" or "sales", use SUM(oi.quantity * oi.unit_price) from order_items.
9. For "recent" or "last month", use date('now', '-1 month') or similar relative dates.

FEW-SHOT EXAMPLES:

Question: What are the top 5 best-selling products?
SQL: SELECT p.name AS product_name, p.category, SUM(oi.quantity) AS total_sold FROM order_items oi JOIN products p ON oi.product_id = p.id GROUP BY p.id, p.name, p.category ORDER BY total_sold DESC LIMIT 5

Question: Show revenue by category
SQL: SELECT p.category, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue FROM order_items oi JOIN products p ON oi.product_id = p.id GROUP BY p.category ORDER BY total_revenue DESC

Question: How many orders were placed each month?
SQL: SELECT strftime('%Y-%m', order_date) AS month, COUNT(*) AS order_count FROM orders GROUP BY month ORDER BY month

Question: What is the average order value by city?
SQL: SELECT u.city, ROUND(AVG(o.total_amount), 2) AS avg_order_value, COUNT(o.id) AS total_orders FROM orders o JOIN users u ON o.user_id = u.id GROUP BY u.city ORDER BY avg_order_value DESC LIMIT 20

Question: Show the order status distribution
SQL: SELECT status, COUNT(*) AS order_count, ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders), 1) AS percentage FROM orders GROUP BY status ORDER BY order_count DESC
"""

CONTEXT_TEMPLATE = """
PREVIOUS CONVERSATION (for follow-up context):
{context}

Use the above context to understand follow-up questions. If the user refers to previous results, adjust the query accordingly.
"""


class SQLGenerator:
    """Generates SQL from natural language using Groq LLM."""

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY not set. Add your key to the .env file.\n"
                "Get one at: https://console.groq.com"
            )
        self.client = Groq(api_key=api_key)
        self.model = model

    def _clean_sql(self, raw: str) -> str:
        """Strip markdown fences and whitespace from LLM output."""
        sql = raw.strip()
        # Remove markdown code fences
        sql = re.sub(r"^```(?:sql)?\s*", "", sql)
        sql = re.sub(r"\s*```$", "", sql)
        return sql.strip()

    def generate_sql(
        self, question: str, schema: str, context: list[dict] | None = None
    ) -> str:
        """Generate SQL from a natural language question."""
        system = SYSTEM_PROMPT.format(schema=schema)

        if context:
            ctx_lines = []
            for entry in context[-5:]:
                ctx_lines.append(f"Q: {entry['question']}")
                ctx_lines.append(f"SQL: {entry['sql']}")
                if entry.get("summary"):
                    ctx_lines.append(f"Result: {entry['summary']}")
                ctx_lines.append("")
            system += CONTEXT_TEMPLATE.format(context="\n".join(ctx_lines))

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
                max_tokens=1024,
            )
            raw_sql = response.choices[0].message.content
            sql = self._clean_sql(raw_sql)
            logger.info(f"Generated SQL for: '{question[:60]}' → {sql[:80]}")
            return sql

        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise RuntimeError(f"Failed to generate SQL: {str(e)}")

    def correct_sql(
        self,
        question: str,
        original_sql: str,
        error: str,
        schema: str,
        context: list[dict] | None = None,
    ) -> str:
        """Attempt to fix a failed SQL query using the error message."""
        system = SYSTEM_PROMPT.format(schema=schema)

        correction_prompt = (
            f"The following SQL query was generated for the question but failed:\n\n"
            f"Question: {question}\n"
            f"Original SQL: {original_sql}\n"
            f"Error: {error}\n\n"
            f"Fix the SQL query. Output ONLY the corrected SQL — no explanations."
        )

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": correction_prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
                max_tokens=1024,
            )
            raw_sql = response.choices[0].message.content
            sql = self._clean_sql(raw_sql)
            logger.info(f"Corrected SQL: {sql[:80]}")
            return sql

        except Exception as e:
            logger.error(f"SQL correction failed: {e}")
            raise RuntimeError(f"Failed to correct SQL: {str(e)}")
