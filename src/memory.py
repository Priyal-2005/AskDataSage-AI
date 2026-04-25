"""
AskDataSage AI — Conversational Memory
Maintains conversation context for follow-up questions using Streamlit session state.
"""

import streamlit as st
from src.logger import get_logger

logger = get_logger("memory")

MAX_HISTORY = 5  # Keep last N conversations


class ConversationMemory:
    """Manages conversation history in Streamlit session state."""

    def __init__(self):
        if "conversation_history" not in st.session_state:
            st.session_state.conversation_history = []

    @property
    def history(self) -> list[dict]:
        return st.session_state.conversation_history

    def add(self, question: str, sql: str, result_summary: str) -> None:
        """Add a Q&A pair to conversation history."""
        entry = {
            "question": question,
            "sql": sql,
            "summary": result_summary,
        }
        st.session_state.conversation_history.append(entry)

        # Trim to max size
        if len(st.session_state.conversation_history) > MAX_HISTORY:
            st.session_state.conversation_history = (
                st.session_state.conversation_history[-MAX_HISTORY:]
            )

        logger.info(
            f"Memory updated: {len(st.session_state.conversation_history)} entries"
        )

    def get_context(self) -> list[dict] | None:
        """Return conversation history for LLM context, or None if empty."""
        if not st.session_state.conversation_history:
            return None
        return st.session_state.conversation_history

    def clear(self) -> None:
        """Clear all conversation history."""
        st.session_state.conversation_history = []
        logger.info("Conversation memory cleared")

    def get_display_history(self) -> list[dict]:
        """Return history formatted for UI display."""
        return list(reversed(st.session_state.conversation_history))
