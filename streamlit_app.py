"""
AskDataSage AI — Streamlit Application
Main entry point for the AI-powered data insights assistant.
"""

import streamlit as st
import pandas as pd
import time

from src.sql_generator import SQLGenerator
from src.query_validator import QueryValidator
from src.query_executor import QueryExecutor
from src.viz_engine import VizEngine
from src.insight_generator import InsightGenerator
from src.memory import ConversationMemory
from src.logger import get_logger

logger = get_logger("app")

# ═══════════════════════════════════════════════════════════════════════════
# Page Configuration
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AskDataSage AI",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
# Custom CSS
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Header gradient */
    .main-header {
        background: linear-gradient(135deg, #6C63FF 0%, #FF6584 50%, #43E97B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.8rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0;
        padding-top: 0.5rem;
    }

    .sub-header {
        text-align: center;
        color: #8B8FA3;
        font-size: 1.05rem;
        font-weight: 300;
        margin-bottom: 2rem;
    }

    /* Insight card */
    .insight-card {
        background: linear-gradient(135deg, #1A1F2E 0%, #252A3A 100%);
        border: 1px solid rgba(108, 99, 255, 0.3);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 0.8rem 0;
        line-height: 1.7;
    }

    .insight-card .insight-icon {
        font-size: 1.3rem;
        margin-right: 0.4rem;
    }

    /* SQL explanation card */
    .sql-explain-card {
        background: linear-gradient(135deg, #1A2332 0%, #1E2D3D 100%);
        border: 1px solid rgba(56, 182, 255, 0.3);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        font-size: 0.95rem;
        color: #B8C9E0;
    }

    /* Sample query buttons */
    .stButton > button {
        border-radius: 8px;
        border: 1px solid rgba(108, 99, 255, 0.4);
        transition: all 0.3s ease;
        font-size: 0.85rem;
    }

    .stButton > button:hover {
        border-color: #6C63FF;
        box-shadow: 0 0 15px rgba(108, 99, 255, 0.3);
        transform: translateY(-1px);
    }

    /* Metrics styling */
    .metric-container {
        background: linear-gradient(135deg, #1A1F2E 0%, #252A3A 100%);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border: 1px solid rgba(108, 99, 255, 0.2);
    }

    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #6C63FF;
    }

    .metric-label {
        font-size: 0.8rem;
        color: #8B8FA3;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* History item */
    .history-item {
        background: rgba(26, 31, 46, 0.6);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid #6C63FF;
        font-size: 0.88rem;
    }

    /* Divider */
    .section-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(108,99,255,0.3), transparent);
        margin: 1.5rem 0;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0E1117 0%, #141820 100%);
    }

    /* Hide default streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Dataframe styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# Initialize Components
# ═══════════════════════════════════════════════════════════════════════════


@st.cache_resource
def init_components():
    """Initialize all backend components (cached)."""
    try:
        executor = QueryExecutor()
        validator = QueryValidator()
        sql_gen = SQLGenerator()
        viz = VizEngine()
        insights = InsightGenerator()
        schema = executor.get_schema()
        return executor, validator, sql_gen, viz, insights, schema, None
    except Exception as e:
        return None, None, None, None, None, None, str(e)


executor, validator, sql_gen, viz, insights, schema, init_error = init_components()
memory = ConversationMemory()

# ═══════════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🔮 AskDataSage AI")
    st.markdown(
        '<p style="color: #8B8FA3; font-size: 0.85rem;">'
        "AI-powered data insights for your e-commerce database</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ---- Sample Queries ----
    st.markdown("#### 💡 Try These Queries")

    sample_queries = [
        ("🏆 Top 5 Products", "What are the top 5 best-selling products?"),
        ("📊 Revenue by Category", "Show total revenue by product category"),
        ("📈 Monthly Trends", "How many orders were placed each month this year?"),
        ("🏙️ Avg Order by City", "What is the average order value by city?"),
        ("👑 Top 10 Customers", "Who are the top 10 customers by total spending?"),
        ("📦 Order Status", "Show the distribution of order statuses"),
    ]

    for label, query in sample_queries:
        if st.button(label, key=f"sample_{label}", use_container_width=True):
            st.session_state.pending_query = query

    st.markdown("---")

    # ---- Actions ----
    st.markdown("#### ⚙️ Actions")

    if st.button("🗑️ Clear History", use_container_width=True):
        memory.clear()
        if "results" in st.session_state:
            del st.session_state.results
        st.rerun()

    # ---- Query History ----
    if memory.history:
        st.markdown("---")
        st.markdown("#### 🕐 Recent Queries")
        for i, entry in enumerate(memory.get_display_history()):
            st.markdown(
                f'<div class="history-item">📝 {entry["question"]}</div>',
                unsafe_allow_html=True,
            )

    # ---- About ----
    st.markdown("---")
    with st.expander("ℹ️ About"):
        st.markdown("""
        **AskDataSage AI** converts your natural language questions
        into SQL queries, executes them, and delivers interactive
        visualizations with business insights.

        **Stack:** Groq LLM · SQLite · Plotly · Streamlit

        **Database:** E-commerce data with users, products,
        orders, and order items.
        """)

# ═══════════════════════════════════════════════════════════════════════════
# Main Content
# ═══════════════════════════════════════════════════════════════════════════

# Header
st.markdown('<h1 class="main-header">AskDataSage AI</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Ask questions about your data in plain English — '
    "get SQL, charts, and insights instantly</p>",
    unsafe_allow_html=True,
)

# Show init error if any
if init_error:
    st.error(f"⚠️ Initialization Error: {init_error}")
    st.info("Please check your `.env` file and ensure the database exists.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# Query Input
# ═══════════════════════════════════════════════════════════════════════════

# Handle pending query from sample buttons
pending = st.session_state.pop("pending_query", None)

question = st.text_input(
    "🔍 Ask a question about your data",
    value=pending or "",
    placeholder="e.g., What are the top 5 products by revenue?",
    key="query_input",
    label_visibility="collapsed",
)

col_ask, col_spacer = st.columns([1, 4])
with col_ask:
    ask_clicked = st.button("🚀 Ask DataSage", type="primary", use_container_width=True)

should_process = ask_clicked and question.strip()

# ═══════════════════════════════════════════════════════════════════════════
# Processing Pipeline
# ═══════════════════════════════════════════════════════════════════════════

if should_process:
    question = question.strip()
    logger.info(f"Processing question: {question}")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    with st.spinner(""):
        # Progress tracking
        progress = st.progress(0, text="🧠 Understanding your question...")
        time.sleep(0.3)

        # ---- Step 1: Generate SQL ----
        progress.progress(15, text="🧠 Generating SQL query...")
        try:
            context = memory.get_context()
            generated_sql = sql_gen.generate_sql(question, schema, context)
        except Exception as e:
            st.error(f"❌ Failed to generate SQL: {str(e)}")
            logger.error(f"SQL generation failed: {e}")
            st.stop()

        # ---- Step 2: Validate SQL ----
        progress.progress(30, text="🛡️ Validating query safety...")
        is_valid, validation_error = validator.validate(generated_sql)

        if not is_valid:
            st.error(f"🛡️ Query Blocked: {validation_error}")
            st.code(generated_sql, language="sql")
            logger.warning(f"Query blocked: {validation_error}")
            st.stop()

        # ---- Step 3: Execute SQL ----
        progress.progress(50, text="⚡ Executing query...")
        df, exec_error = executor.execute(generated_sql)

        original_sql = generated_sql
        corrected_sql = None

        # ---- Step 3b: Correction Loop (if execution fails) ----
        if exec_error:
            progress.progress(55, text="🔧 Query failed — attempting correction...")
            logger.info(f"Attempting SQL correction for error: {exec_error}")

            try:
                corrected_sql = sql_gen.correct_sql(
                    question, generated_sql, exec_error, schema, context
                )

                # Validate corrected SQL
                is_valid2, val_err2 = validator.validate(corrected_sql)
                if is_valid2:
                    df, exec_error2 = executor.execute(corrected_sql)
                    if exec_error2:
                        st.error(f"❌ Query failed even after correction: {exec_error2}")
                        st.code(corrected_sql, language="sql")
                        st.stop()
                    else:
                        generated_sql = corrected_sql
                        exec_error = None
                else:
                    st.error(f"❌ Corrected query also invalid: {val_err2}")
                    st.stop()
            except Exception as e:
                st.error(f"❌ Query correction failed: {str(e)}")
                st.code(generated_sql, language="sql")
                st.stop()

        if exec_error:
            st.error(f"❌ Query execution failed: {exec_error}")
            st.code(generated_sql, language="sql")
            st.stop()

        # ---- Step 4: Explain SQL ----
        progress.progress(65, text="📖 Explaining the query...")
        try:
            sql_explanation = insights.explain_sql(generated_sql)
        except Exception:
            sql_explanation = ""

        # ---- Step 5: Generate Visualization ----
        progress.progress(80, text="📊 Creating visualization...")
        chart = viz.generate_chart(df, question)

        # ---- Step 6: Generate Insight ----
        progress.progress(90, text="💡 Generating business insights...")
        try:
            # Create result summary for memory
            if len(df) <= 5:
                result_summary = df.to_string(index=False)
            else:
                result_summary = (
                    f"{len(df)} rows returned. "
                    f"Columns: {', '.join(df.columns.tolist())}. "
                    f"Sample: {df.head(3).to_string(index=False)}"
                )

            insight_text = insights.generate_insight(question, generated_sql, df)
        except Exception:
            insight_text = ""
            result_summary = f"{len(df)} rows returned"

        # ---- Step 7: Update Memory ----
        memory.add(question, generated_sql, result_summary)

        progress.progress(100, text="✅ Done!")
        time.sleep(0.3)
        progress.empty()

    # ═══════════════════════════════════════════════════════════════════
    # Display Results
    # ═══════════════════════════════════════════════════════════════════

    # ---- SQL Query ----
    with st.expander("🔍 SQL Query" + (" (corrected)" if corrected_sql else ""), expanded=False):
        if corrected_sql:
            st.markdown("**Original SQL** (failed):")
            st.code(original_sql, language="sql")
            st.markdown("**Corrected SQL:**")
        st.code(generated_sql, language="sql")

    # ---- SQL Explanation ----
    if sql_explanation:
        st.markdown(
            f'<div class="sql-explain-card">📖 <strong>What this query does:</strong> {sql_explanation}</div>',
            unsafe_allow_html=True,
        )

    # ---- Results Table ----
    st.markdown("#### 📋 Results")

    # Show metrics for small results
    if len(df) == 1 and len(df.columns) <= 4:
        cols = st.columns(len(df.columns))
        for i, col_name in enumerate(df.columns):
            with cols[i]:
                value = df.iloc[0][col_name]
                if isinstance(value, float):
                    value = f"{value:,.2f}"
                st.markdown(
                    f'<div class="metric-container">'
                    f'<div class="metric-value">{value}</div>'
                    f'<div class="metric-label">{col_name}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=min(400, 35 * len(df) + 38),
        )
        st.caption(f"Showing {len(df)} rows × {len(df.columns)} columns")

    # ---- Download CSV ----
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download as CSV",
        data=csv_data,
        file_name="askdatasage_results.csv",
        mime="text/csv",
    )

    # ---- Chart ----
    if chart:
        st.markdown("#### 📊 Visualization")
        st.plotly_chart(chart, use_container_width=True, theme=None)

    # ---- Business Insight ----
    if insight_text:
        st.markdown("#### 💡 Business Insight")
        st.markdown(
            f'<div class="insight-card">'
            f'<span class="insight-icon">🧠</span> {insight_text}'
            f"</div>",
            unsafe_allow_html=True,
        )

    logger.info(f"Pipeline completed for: {question}")
