"""
AskDataSage AI — Input Validator
Validates user input before sending to the LLM pipeline.
Rejects empty, too-short, or clearly irrelevant queries.
"""

import re
from src.logger import get_logger

logger = get_logger("input_validator")

MIN_QUESTION_LENGTH = 5
MAX_QUESTION_LENGTH = 500

# Keywords that suggest a data-related question
DATA_KEYWORDS = [
    "show", "list", "find", "get", "what", "which", "who", "how",
    "many", "much", "count", "total", "average", "sum", "top",
    "best", "worst", "highest", "lowest", "most", "least",
    "revenue", "sales", "orders", "products", "customers", "users",
    "category", "status", "month", "year", "date", "price",
    "compare", "between", "trend", "distribution", "breakdown",
    "by", "per", "each", "all", "recent", "last", "first",
    "expensive", "popular", "selling", "bought", "spent",
    "city", "name", "email", "quantity", "amount", "order",
    "item", "stock", "pending", "completed", "cancelled",
    "give", "display", "tell", "calculate", "number",
]

# Patterns that are clearly not data questions
IRRELEVANT_PATTERNS = [
    r"^(hi|hello|hey|yo|sup)\b",
    r"^(thanks|thank you|bye|goodbye)",
    r"^(who are you|what are you|your name)",
    r"^(write|code|program|build|create|make)\b.*(app|website|program|script|code|function)",
    r"^(tell me a joke|sing|poem|story)",
]

SUGGESTION_TEXT = (
    "💡 **Try asking about your data**, for example:\n"
    '- "What are the top 5 products by revenue?"\n'
    '- "Show monthly order trends"\n'
    '- "Revenue by category"\n'
    '- "Average order value by city"\n'
    '- "Which customers spent the most?"'
)


class InputValidator:
    """Validates user questions before processing."""

    def validate(self, question: str) -> tuple[bool, str]:
        """
        Validate user input.

        Returns:
            (is_valid, error_message) — error_message includes suggestions when invalid.
        """
        if not question or not question.strip():
            return False, f"Please enter a question.\n\n{SUGGESTION_TEXT}"

        q = question.strip()

        # Too short
        if len(q) < MIN_QUESTION_LENGTH:
            logger.warning(f"Question too short: '{q}'")
            return False, f"Your question is too short. Please be more specific.\n\n{SUGGESTION_TEXT}"

        # Too long
        if len(q) > MAX_QUESTION_LENGTH:
            logger.warning(f"Question too long: {len(q)} chars")
            return False, (
                f"Your question is too long ({len(q)} characters). "
                f"Please keep it under {MAX_QUESTION_LENGTH} characters."
            )

        # Check for clearly irrelevant patterns
        q_lower = q.lower()
        for pattern in IRRELEVANT_PATTERNS:
            if re.match(pattern, q_lower):
                logger.info(f"Irrelevant input rejected: '{q[:50]}'")
                return False, (
                    "That doesn't look like a data question. "
                    "I'm designed to help you explore your e-commerce database.\n\n"
                    f"{SUGGESTION_TEXT}"
                )

        # Check if question contains at least one data-related keyword
        has_data_keyword = any(kw in q_lower for kw in DATA_KEYWORDS)
        if not has_data_keyword:
            # Allow it through with a soft warning — the LLM might still handle it
            logger.info(f"No data keywords found, but allowing: '{q[:50]}'")

        logger.info(f"Input validated: '{q[:60]}'")
        return True, ""
