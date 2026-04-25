"""
AskDataSage AI — Insight Generator
Generates business insights and SQL explanations using Groq LLM.
Includes LLM timeout control and response caching.
"""

import os
import hashlib
import time

from groq import Groq
from dotenv import load_dotenv
import pandas as pd

from src.logger import get_logger

load_dotenv()
logger = get_logger("insights")

LLM_TIMEOUT_SECONDS = 30

INSIGHT_PROMPT = """You are a senior business data analyst. Based on the question, SQL query, and actual query results below, provide a concise business insight.

QUESTION: {question}

SQL QUERY: {sql}

QUERY RESULTS (first {num_rows} rows):
{data}

RULES:
1. Provide 2-4 sentences of insight.
2. Reference ONLY the actual data shown — never hallucinate or invent numbers.
3. Highlight key trends, comparisons, percentages, or patterns.
4. Use specific numbers from the data.
5. If there's a notable finding (e.g., one category dominates), call it out.
6. Write in a professional but accessible tone.
7. Do NOT repeat the question or describe what the query does.

INSIGHT:"""

SQL_EXPLAIN_PROMPT = """You are a SQL teacher. Explain this SQL query in simple, non-technical language that a business user can understand.

SQL QUERY:
{sql}

RULES:
1. Use 1-2 short sentences.
2. Focus on WHAT the query finds, not HOW it works technically.
3. Mention the tables/data being looked at in business terms.
4. Do NOT use technical jargon like JOIN, GROUP BY, etc.

EXPLANATION:"""


class InsightGenerator:
    """Generates business insights and SQL explanations via LLM with caching."""

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            raise ValueError("GROQ_API_KEY not configured.")
        self.client = Groq(api_key=api_key)
        self.model = model
        # Caches
        self._insight_cache: dict[str, str] = {}
        self._explain_cache: dict[str, str] = {}

    def _call_llm(
        self, messages: list[dict], temperature: float = 0.3, max_tokens: int = 512
    ) -> str:
        """Call Groq LLM with timeout protection."""
        start = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=LLM_TIMEOUT_SECONDS,
            )
            elapsed = round(time.time() - start, 2)
            content = response.choices[0].message.content.strip()
            logger.info(f"LLM insight response in {elapsed}s")
            return content
        except Exception as e:
            elapsed = round(time.time() - start, 2)
            if elapsed >= LLM_TIMEOUT_SECONDS:
                raise RuntimeError(
                    f"LLM request timed out after {LLM_TIMEOUT_SECONDS}s."
                )
            raise

    def generate_insight(
        self, question: str, sql: str, df: pd.DataFrame
    ) -> str:
        """Generate a business insight based on query results. Cached by question+SQL."""
        cache_key = hashlib.md5(f"{question}|{sql}".encode()).hexdigest()
        if cache_key in self._insight_cache:
            logger.info("Insight cache hit")
            return self._insight_cache[cache_key]

        try:
            # Prepare data summary (limit to 50 rows for prompt size)
            num_rows = min(len(df), 50)
            data_str = df.head(num_rows).to_markdown(index=False)

            prompt = INSIGHT_PROMPT.format(
                question=question,
                sql=sql,
                num_rows=num_rows,
                data=data_str,
            )

            insight = self._call_llm(
                [{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=512,
            )
            logger.info(f"Insight generated: {insight[:80]}...")
            self._insight_cache[cache_key] = insight
            return insight

        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return "Unable to generate insight at this time."

    def explain_sql(self, sql: str) -> str:
        """Explain a SQL query in plain English. Cached by SQL text."""
        cache_key = hashlib.md5(sql.encode()).hexdigest()
        if cache_key in self._explain_cache:
            logger.info("SQL explain cache hit")
            return self._explain_cache[cache_key]

        try:
            prompt = SQL_EXPLAIN_PROMPT.format(sql=sql)

            explanation = self._call_llm(
                [{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=256,
            )
            logger.info(f"SQL explained: {explanation[:80]}...")
            self._explain_cache[cache_key] = explanation
            return explanation

        except Exception as e:
            logger.error(f"SQL explanation failed: {e}")
            return "Unable to explain the query at this time."
