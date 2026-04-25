"""
AskDataSage AI — Streamlit Application
Major UX Upgrade: Custom Data Upload, Dual Mode, and UI Redesign.
"""

import os
import time

import pandas as pd
import streamlit as st

from src.data_loader import DataLoader, DataLoadError
from src.insight_generator import InsightGenerator
from src.input_validator import InputValidator
from src.logger import get_logger
from src.memory import ConversationMemory
from src.query_executor import QueryExecutor, DEFAULT_DB_PATH
from src.query_validator import QueryValidator
from src.sql_generator import SQLGenerator
from src.viz_engine import VizEngine

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
# Custom CSS (Glassmorphism, Chat UI, Redesign)
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hero Section */
    .hero-container {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 1rem;
    }
    .main-title {
        background: linear-gradient(135deg, #6C63FF 0%, #FF6584 50%, #43E97B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.2;
    }
    .sub-title {
        color: #A0AEC0;
        font-size: 1.2rem;
        font-weight: 300;
        margin-top: 0.5rem;
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Chat UI */
    .chat-bubble-user {
        background: linear-gradient(135deg, #6C63FF 0%, #8B5CF6 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 0 20px;
        margin: 1rem 0 1.5rem auto;
        max-width: 80%;
        width: fit-content;
        box-shadow: 0 4px 15px rgba(108, 99, 255, 0.3);
        font-size: 1.05rem;
        font-weight: 500;
    }

    .chat-container-ai {
        background: rgba(20, 24, 36, 0.6);
        border: 1px solid rgba(108, 99, 255, 0.2);
        border-radius: 0 20px 20px 20px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }

    /* Insight Block */
    .insight-block {
        font-size: 1.1rem;
        line-height: 1.6;
        color: #E2E8F0;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: flex-start;
        gap: 0.8rem;
    }
    .insight-block span {
        font-size: 1.5rem;
    }

    /* Context Badge */
    .context-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(67, 233, 123, 0.15);
        color: #43E97B;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid rgba(67, 233, 123, 0.3);
        margin-bottom: 2rem;
    }
    .context-badge.upload-mode {
        background: rgba(255, 101, 132, 0.15);
        color: #FF6584;
        border-color: rgba(255, 101, 132, 0.3);
    }

    /* Buttons */
    .stButton > button {
        border-radius: 12px;
        border: 1px solid rgba(108, 99, 255, 0.5);
        transition: all 0.2s ease;
        background: rgba(108, 99, 255, 0.1);
        color: white;
    }
    .stButton > button:hover {
        border-color: #6C63FF;
        background: rgba(108, 99, 255, 0.2);
        box-shadow: 0 0 20px rgba(108, 99, 255, 0.4);
        transform: translateY(-2px);
    }

    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sidebar Tweaks */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B0F19 0%, #1A1F2E 100%);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# Session State & Initialization
# ═══════════════════════════════════════════════════════════════════════════

if "mode" not in st.session_state:
    st.session_state.mode = "demo"  # 'demo' or 'upload'
if "user_data_info" not in st.session_state:
    st.session_state.user_data_info = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "demo_schema" not in st.session_state:
    st.session_state.demo_schema = None
if "demo_db_info" not in st.session_state:
    st.session_state.demo_db_info = None

@st.cache_resource
def get_backend_tools():
    return (
        QueryValidator(),
        InputValidator(),
        SQLGenerator(),
        VizEngine(),
        InsightGenerator(),
        DataLoader()
    )

(
    validator, input_val, sql_gen, viz, insights, data_loader
) = get_backend_tools()

memory = ConversationMemory()

# Initialize demo schema if needed
if not st.session_state.demo_schema:
    try:
        demo_exec = QueryExecutor(DEFAULT_DB_PATH)
        st.session_state.demo_schema = demo_exec.get_schema_for_llm()
        st.session_state.demo_db_info = demo_exec.get_structured_schema()
    except Exception as e:
        st.error(f"Failed to load demo database: {e}")

# Helper to get current execution context
def get_current_context():
    if st.session_state.mode == "demo":
        return DEFAULT_DB_PATH, st.session_state.demo_schema, st.session_state.demo_db_info
    else:
        info = st.session_state.user_data_info
        if info:
            return info["db_path"], info["schema_str"], [{"name": info["table_name"], "row_count": info["row_count"], "columns": info["columns"]}]
        return None, None, None

# ═══════════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Data Source")
    
    # Mode Toggle
    mode_index = 0 if st.session_state.mode == "demo" else 1
    mode = st.radio(
        "Select Mode",
        ["Demo Database", "Upload Your Data"],
        index=mode_index,
        label_visibility="collapsed"
    )
    
    new_mode = "demo" if mode == "Demo Database" else "upload"
    if new_mode != st.session_state.mode:
        st.session_state.mode = new_mode
        st.session_state.last_result = None
        memory.clear()
        st.rerun()

    st.markdown("---")

    if st.session_state.mode == "upload":
        st.markdown("#### 📤 Upload CSV")
        uploaded_file = st.file_uploader("Max size: 10MB", type=["csv"], label_visibility="collapsed")
        
        if uploaded_file is not None:
            # Need to process upload? (Check if it's new)
            if not st.session_state.user_data_info or st.session_state.user_data_info.get("filename") != uploaded_file.name:
                with st.spinner("Processing data..."):
                    try:
                        info = data_loader.load_csv(uploaded_file)
                        info["filename"] = uploaded_file.name
                        st.session_state.user_data_info = info
                        st.session_state.last_result = None
                        memory.clear()
                        st.success("Data loaded successfully!")
                        time.sleep(1)
                        st.rerun()
                    except DataLoadError as e:
                        st.error(f"Upload failed: {e}")
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")
        
        if st.session_state.user_data_info:
            info = st.session_state.user_data_info
            st.markdown(f"**Loaded:** `{info['filename']}`")
            st.markdown(f"**Rows:** {info['row_count']:,} | **Cols:** {info['col_count']}")
            with st.expander("Preview Columns"):
                for col in info["columns"]:
                    st.caption(f"- `{col['name']}` ({col['type']})")
    
    else:
        # Demo Info
        st.markdown("#### 🛒 Demo Database")
        db_info = st.session_state.demo_db_info
        if db_info:
            total_rows = sum(t["row_count"] for t in db_info)
            st.caption(f"E-commerce data | {len(db_info)} tables | {total_rows:,} rows")
            with st.expander("View Tables"):
                for t in db_info:
                    st.caption(f"**{t['name']}** ({t['row_count']} rows)")

    st.markdown("---")

    # Quick Suggestions
    st.markdown("#### 💡 Suggestions")
    suggestions = []
    if st.session_state.mode == "demo":
        suggestions = [
            ("🏆 Top Products", "What are the top 5 best-selling products?"),
            ("📈 Monthly Trends", "How many orders were placed each month this year?"),
            ("🏙️ Avg Order by City", "What is the average order value by city?"),
        ]
    elif st.session_state.user_data_info:
        suggestions = st.session_state.user_data_info.get("suggestions", [])

    for label, query in suggestions:
        if st.button(label, key=f"sugg_{label}", use_container_width=True):
            st.session_state.triggered_query = query
            st.rerun()

    # History
    if memory.history:
        st.markdown("---")
        st.markdown("#### 🕒 History")
        for entry in memory.get_display_history()[-3:]:
            st.caption(f"📝 {entry['question'][:40]}...")
        if st.button("Clear History", use_container_width=True):
            memory.clear()
            st.session_state.last_result = None
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# Main UI
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="hero-container">
    <h1 class="main-title">AskDataSage AI</h1>
    <p class="sub-title">Your AI Data Analyst</p>
</div>
""", unsafe_allow_html=True)

# Context Badge
if st.session_state.mode == "demo":
    st.markdown('<div align="center"><span class="context-badge">📊 Using Demo Dataset</span></div>', unsafe_allow_html=True)
else:
    if st.session_state.user_data_info:
        fname = st.session_state.user_data_info['filename']
        st.markdown(f'<div align="center"><span class="context-badge upload-mode">📤 Using {fname}</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div align="center"><span class="context-badge upload-mode">⚠️ Please upload a CSV in the sidebar</span></div>', unsafe_allow_html=True)
        st.stop()


# ═══════════════════════════════════════════════════════════════════════════
# Query Execution Logic
# ═══════════════════════════════════════════════════════════════════════════

question = st.chat_input("Ask a question about your data...", key="chat_input")
triggered = st.session_state.pop("triggered_query", None)

if triggered:
    question = triggered

if question:
    question = question.strip()
    
    # Store question immediately to display user bubble
    st.session_state.current_q = question
    
    pipeline_start = time.time()
    
    db_path, schema_str, _ = get_current_context()
    executor = QueryExecutor(db_path)
    
    # 1. Validation
    is_valid_input, input_error = input_val.validate(question)
    if not is_valid_input:
        st.error(f"Input Error: {input_error}")
        st.stop()
        
    with st.spinner("🤖 AI is analyzing your data..."):
        # 2. Generate SQL
        try:
            ctx = memory.get_context()
            sql = sql_gen.generate_sql(question, schema_str, ctx)
        except Exception as e:
            st.error(f"SQL Generation Error: {e}")
            st.stop()
            
        # 3. Validate SQL
        is_valid_sql, sql_err = validator.validate(sql)
        if not is_valid_sql:
            st.error(f"Security Blocked: {sql_err}")
            st.stop()
            
        # 4. Execute SQL
        df, exec_err = executor.execute(sql)
        original_sql = sql
        corrected_sql = None
        
        if exec_err:
            try:
                corrected_sql = sql_gen.correct_sql(question, sql, exec_err, schema_str, ctx)
                if validator.validate(corrected_sql)[0]:
                    df, exec_err = executor.execute(corrected_sql)
                    sql = corrected_sql
            except Exception:
                pass
                
        if exec_err:
            st.error(f"Execution Error: {exec_err}")
            st.code(sql, language="sql")
            st.stop()
            
        is_empty = df is not None and df.empty
        
        # 5. Explain & Viz & Insight
        explanation = insights.explain_sql(sql) if not is_empty else ""
        chart = viz.generate_chart(df, question) if not is_empty else None
        insight_text = ""
        
        if not is_empty:
            try:
                insight_text = insights.generate_insight(question, sql, df)
            except Exception:
                pass
                
        # 6. Save State
        mem_summary = f"{len(df)} rows returned" if df is not None else "Error"
        memory.add(question, sql, mem_summary)
        
        elapsed = round(time.time() - pipeline_start, 2)
        
        st.session_state.last_result = {
            "q": question,
            "sql": sql,
            "orig_sql": original_sql,
            "corr_sql": corrected_sql,
            "df": df,
            "chart": chart,
            "explanation": explanation,
            "insight": insight_text,
            "empty": is_empty,
            "time": elapsed
        }

# ═══════════════════════════════════════════════════════════════════════════
# Result Rendering (Chat UI)
# ═══════════════════════════════════════════════════════════════════════════

res = st.session_state.last_result

if res:
    # User Bubble
    st.markdown(f'<div class="chat-bubble-user">{res["q"]}</div>', unsafe_allow_html=True)
    
    # AI Container
    with st.container():
        st.markdown('<div class="chat-container-ai">', unsafe_allow_html=True)
        
        if res["empty"]:
            st.info("📭 No results found for this query.")
        else:
            # 1. Insight
            if res["insight"]:
                st.markdown(f'<div class="insight-block"><span>💡</span><div>{res["insight"]}</div></div>', unsafe_allow_html=True)
            
            # 2. Chart
            if res["chart"]:
                st.plotly_chart(res["chart"], use_container_width=True, theme=None)
                st.markdown("<br>", unsafe_allow_html=True)
            
            # 3. Data & SQL Expanders
            col1, col2 = st.columns(2)
            with col1:
                with st.expander("📄 Data Table"):
                    st.dataframe(res["df"], use_container_width=True, hide_index=True)
                    csv = res["df"].to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Download CSV", csv, "results.csv", "text/csv", use_container_width=True)
            with col2:
                with st.expander("🧾 SQL Query & Details"):
                    st.markdown("**Executed SQL:**")
                    st.code(res["sql"], language="sql")
                    if res["corr_sql"]:
                        st.warning("Query was automatically corrected after an error.")
                    if res["explanation"]:
                        st.markdown("**Explanation:**")
                        st.info(res["explanation"])
                    st.caption(f"⏱️ Executed in {res['time']}s")

        st.markdown('</div>', unsafe_allow_html=True)
else:
    # Empty State
    st.markdown("""
    <div style="text-align: center; margin-top: 4rem; color: #475569;">
        <h2 style="font-weight: 300;">Ready to explore your data?</h2>
        <p>Type a question in the chat box below to get started.</p>
    </div>
    """, unsafe_allow_html=True)