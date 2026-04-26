"""
AskDataSage AI — Streamlit Application
Final Production Upgrade: Elite UI/UX, Robust Fallbacks, and Polished Architecture.
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
from data.database import init_database, get_debug_info

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
# Elite CSS (Glassmorphism, Animations, Dark Mode Perfection)
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hero Section with Animation */
    .hero-container {
        text-align: center;
        padding: 3rem 0 1.5rem 0;
        animation: fadeInDown 0.8s ease-out;
    }
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main-title {
        background: linear-gradient(135deg, #6C63FF 0%, #FF6584 50%, #43E97B 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 4rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.1;
        animation: gradientShimmer 3s ease infinite;
    }
    @keyframes gradientShimmer {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .sub-title {
        color: #94A3B8;
        font-size: 1.3rem;
        font-weight: 400;
        margin-top: 0.5rem;
        letter-spacing: 0.5px;
    }

    /* Chat UI */
    .chat-bubble-user {
        background: linear-gradient(135deg, #6C63FF 0%, #8B5CF6 100%);
        color: white;
        padding: 1.2rem 1.8rem;
        border-radius: 24px 24px 4px 24px;
        margin: 1.5rem 0 2rem auto;
        max-width: 75%;
        width: fit-content;
        box-shadow: 0 8px 20px rgba(108, 99, 255, 0.25);
        font-size: 1.1rem;
        font-weight: 500;
        animation: slideInRight 0.4s ease-out;
    }
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }

    /* AI Response Card (Glassmorphism + Hover) */
    .chat-container-ai {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 4px 24px 24px 24px;
        padding: 2rem;
        margin-bottom: 3rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        animation: slideInLeft 0.5s ease-out;
    }
    .chat-container-ai:hover {
        transform: scale(1.005) translateY(-2px);
        box-shadow: 0 15px 40px rgba(108, 99, 255, 0.15);
        border-color: rgba(108, 99, 255, 0.3);
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }

    /* Visual Hierarchy Components */
    .insight-block {
        font-size: 1.2rem;
        line-height: 1.7;
        color: #F8FAFC;
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        display: flex;
        align-items: flex-start;
        gap: 1rem;
    }
    .insight-icon {
        font-size: 1.8rem;
        filter: drop-shadow(0 0 8px rgba(108, 99, 255, 0.4));
    }
    
    /* Empty State */
    .empty-state-card {
        background: rgba(30, 41, 59, 0.3);
        border: 1px dashed rgba(108, 99, 255, 0.4);
        border-radius: 20px;
        padding: 4rem 2rem;
        text-align: center;
        margin-top: 2rem;
        transition: all 0.3s;
    }
    .empty-state-card:hover {
        background: rgba(30, 41, 59, 0.5);
        border-color: rgba(108, 99, 255, 0.8);
    }

    /* Active Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.4rem 0.8rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .badge-demo {
        background: rgba(67, 233, 123, 0.15);
        color: #43E97B;
        border: 1px solid rgba(67, 233, 123, 0.3);
    }
    .badge-upload {
        background: rgba(108, 99, 255, 0.15);
        color: #A78BFA;
        border: 1px solid rgba(108, 99, 255, 0.3);
    }

    /* Buttons */
    .stButton > button {
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.05);
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: rgba(108, 99, 255, 0.15);
        border-color: rgba(108, 99, 255, 0.5);
        box-shadow: 0 0 15px rgba(108, 99, 255, 0.3);
        color: white;
    }
    
    /* Expander Tweaks */
    .streamlit-expanderHeader {
        background-color: transparent !important;
        font-weight: 600;
        color: #94A3B8;
    }

    /* Clean UI Overrides */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    
    .footer {
        position: fixed;
        bottom: 10px;
        right: 20px;
        font-size: 0.8rem;
        color: #64748B;
    }
    
    section[data-testid="stSidebar"] {
        background: #0B0F19;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# Initialization & State Safe Handling
# ═══════════════════════════════════════════════════════════════════════════

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

try:
    (validator, input_val, sql_gen, viz, insights, data_loader) = get_backend_tools()
except Exception as e:
    st.error(f"Critical System Failure: Could not initialize AI tools. {e}")
    st.stop()

if "memory" not in st.session_state:
    st.session_state.memory = ConversationMemory()

if "mode" not in st.session_state:
    st.session_state.mode = "demo"
if "user_data_info" not in st.session_state:
    st.session_state.user_data_info = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "demo_schema" not in st.session_state:
    st.session_state.demo_schema = None
if "demo_db_info" not in st.session_state:
    st.session_state.demo_db_info = None
if "ui_settings" not in st.session_state:
    st.session_state.ui_settings = {"show_sql": False, "show_insight": True}

# Initialize demo schema safely
if not st.session_state.demo_schema:
    try:
        with st.spinner("Initializing demo database (this may take a moment)..."):
            db_path = init_database()
            demo_exec = QueryExecutor(db_path)
            st.session_state.demo_schema = demo_exec.get_schema_for_llm()
            st.session_state.demo_db_info = demo_exec.get_structured_schema()
    except Exception as e:
        logger.error(f"Demo DB init failed: {e}")

def get_current_context():
    """Safely retrieves current DB path and schema based on mode."""
    if st.session_state.mode == "demo":
        if not st.session_state.demo_schema:
            return None, None, None
        return init_database(), st.session_state.demo_schema, st.session_state.demo_db_info
    else:
        info = st.session_state.user_data_info
        if info:
            return info["db_path"], info["schema_str"], [{"name": info["table_name"], "row_count": info["row_count"], "columns": info["columns"]}]
        return None, None, None

def reset_chat():
    st.session_state.memory.clear()
    st.session_state.last_result = None
    st.session_state.triggered_query = None

# ═══════════════════════════════════════════════════════════════════════════
# Sidebar (Control Panel)
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎛️ Control Panel")
    
    # Mode Toggle Section
    st.markdown("### 1. Data Mode")
    if st.session_state.mode == "demo":
        st.markdown('<div class="status-badge badge-demo">🟢 Demo Mode Active</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge badge-upload">🟣 Custom Data Active</div>', unsafe_allow_html=True)

    mode_index = 0 if st.session_state.mode == "demo" else 1
    selected_mode = st.radio(
        "Select Mode",
        ["Demo Database", "Upload Your Data"],
        index=mode_index,
        label_visibility="collapsed"
    )
    
    new_mode = "demo" if selected_mode == "Demo Database" else "upload"
    if new_mode != st.session_state.mode:
        st.session_state.mode = new_mode
        reset_chat()
        st.rerun()

    st.markdown("---")

    # DB Info & Upload Section
    st.markdown("### 2. Database Info")
    if st.session_state.mode == "upload":
        uploaded_file = st.file_uploader("Upload CSV (Max 10MB)", type=["csv"], label_visibility="collapsed")
        
        if uploaded_file is not None:
            if not st.session_state.user_data_info or st.session_state.user_data_info.get("filename") != uploaded_file.name:
                with st.spinner("Processing dataset..."):
                    try:
                        info = data_loader.load_csv(uploaded_file)
                        info["filename"] = uploaded_file.name
                        st.session_state.user_data_info = info
                        reset_chat()
                        st.success("✅ Dataset ready!")
                        time.sleep(0.8)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Upload failed: {e}")
        
        if st.session_state.user_data_info:
            info = st.session_state.user_data_info
            st.caption(f"**File:** {info['filename']}")
            st.caption(f"**Shape:** {info['row_count']:,} rows × {info['col_count']} cols")
            with st.expander("View Schema"):
                for col in info["columns"]:
                    st.text(f"• {col['name']} ({col['type']})")
    else:
        db_info = st.session_state.demo_db_info
        if db_info:
            total_rows = sum(t["row_count"] for t in db_info)
            st.caption(f"**Source:** E-commerce System")
            st.caption(f"**Shape:** {len(db_info)} tables, {total_rows:,} rows")
            with st.expander("View Schema"):
                for t in db_info:
                    st.text(f"• {t['name']} ({t['row_count']} rows)")

    st.markdown("---")

    # Quick Questions Section
    st.markdown("### 3. Quick Questions")
    suggestions = []
    if st.session_state.mode == "demo":
        suggestions = [
            "🏆 Top 5 best-selling products?",
            "📊 Total revenue by category?",
            "👑 Top 10 customers by spending?",
            "📦 Distribution of order statuses"
        ]
    elif st.session_state.user_data_info:
        suggestions = [q for _, q in st.session_state.user_data_info.get("suggestions", [])]

    for q in suggestions:
        if st.button(q, use_container_width=True):
            st.session_state.triggered_query = q
            st.rerun()

    st.markdown("---")
    
    # Settings Section
    st.markdown("### 4. Settings")
    st.session_state.ui_settings["show_insight"] = st.toggle("Generate AI Insights", value=st.session_state.ui_settings["show_insight"])
    st.session_state.ui_settings["show_sql"] = st.toggle("Show SQL by default", value=st.session_state.ui_settings["show_sql"])
    
    if st.button("🗑️ Clear Conversation", use_container_width=True, type="secondary"):
        reset_chat()
        st.rerun()

    st.markdown("---")
    
    with st.expander("🛠️ Debug Info"):
        info = get_debug_info()
        st.json(info)

# ═══════════════════════════════════════════════════════════════════════════
# Main UI - Hero & Empty State
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="hero-container">
    <h1 class="main-title">AskDataSage AI</h1>
    <p class="sub-title">Turn Data into Decisions — Instantly</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# Query Execution Flow
# ═══════════════════════════════════════════════════════════════════════════

question = st.chat_input("Ask anything about your data...", key="chat_input")
triggered = st.session_state.pop("triggered_query", None)

if triggered:
    question = triggered

# Stop execution if DB isn't ready
db_path, schema_str, _ = get_current_context()
if not db_path or not schema_str:
    if st.session_state.mode == "upload":
        st.warning("⚠️ Please upload a CSV dataset in the sidebar to begin.")
    else:
        st.error("⚠️ Demo database failed to initialize. Please check logs.")
    st.stop()

if question:
    question = question.strip()
    if not question:
        st.stop()
        
    st.session_state.current_q = question
    pipeline_start = time.time()
    executor = QueryExecutor(db_path)
    
    # --- Step 1: Validation ---
    is_valid_input, input_error = input_val.validate(question)
    if not is_valid_input:
        st.error(f"🛑 Security Block: {input_error}")
        st.stop()
        
    # Container for loading states
    status_container = st.empty()
    
    # Initialize results dict
    result_state = {
        "q": question, "sql": None, "df": None, "chart": None, 
        "insight": None, "explanation": None, "empty": False, 
        "error": None, "fallback": False
    }
    
    try:
        with status_container.status("🧠 Analyzing request...", expanded=True) as status:
            ctx = st.session_state.memory.get_context()
            
            # --- Step 2: Generate SQL (with Fallback) ---
            status.update(label="Generating SQL query...", state="running")
            try:
                sql = sql_gen.generate_sql(question, schema_str, ctx)
                result_state["sql"] = sql
            except Exception as e:
                logger.error(f"LLM SQL Generation failed: {e}")
                result_state["error"] = "AI temporarily unavailable for SQL generation."
                result_state["fallback"] = True
                raise RuntimeError("LLM Failure")
                
            # --- Step 3: Validate SQL ---
            status.update(label="Validating query safety...", state="running")
            is_valid_sql, sql_err = validator.validate(sql)
            if not is_valid_sql:
                result_state["error"] = f"Query Validation Failed: {sql_err}"
                raise ValueError("Unsafe SQL")
                
            # --- Step 4: Execute SQL ---
            status.update(label="Executing query on database...", state="running")
            df, exec_err = executor.execute(sql)
            
            # Correction loop
            if exec_err:
                status.update(label="Fixing query syntax...", state="running")
                try:
                    corrected_sql = sql_gen.correct_sql(question, sql, exec_err, schema_str, ctx)
                    if validator.validate(corrected_sql)[0]:
                        df, exec_err = executor.execute(corrected_sql)
                        if not exec_err:
                            result_state["sql"] = corrected_sql
                except Exception:
                    pass
                    
            if exec_err:
                result_state["error"] = "Query execution failed on the database."
                raise ValueError("Execution Failed")
                
            result_state["df"] = df
            result_state["empty"] = df is None or df.empty
            
            # --- Step 5: Insights & Viz (with Fallback) ---
            if not result_state["empty"]:
                status.update(label="Creating visualizations...", state="running")
                result_state["chart"] = viz.generate_chart(df, question)
                
                if st.session_state.ui_settings["show_insight"]:
                    status.update(label="Generating business insights...", state="running")
                    try:
                        result_state["insight"] = insights.generate_insight(question, result_state["sql"], df)
                        result_state["explanation"] = insights.explain_sql(result_state["sql"])
                    except Exception as e:
                        logger.warning(f"Insight generation failed: {e}")
                        result_state["fallback"] = True
                        result_state["insight"] = "⚠️ AI insights currently unavailable. Raw data is displayed below."
            
            status.update(label="Complete!", state="complete", expanded=False)
            
    except Exception as e:
        # Errors already captured in result_state
        status.update(label="Process interrupted", state="error")
        logger.error(f"Pipeline Exception: {e}")

    # --- Step 6: Finalize State ---
    status_container.empty() # Remove loading spinner
    
    # Save memory
    mem_summary = f"{len(result_state['df'])} rows" if result_state['df'] is not None else "Error"
    st.session_state.memory.add(question, result_state.get('sql', ''), mem_summary)
    
    result_state["time"] = round(time.time() - pipeline_start, 2)
    st.session_state.last_result = result_state

# ═══════════════════════════════════════════════════════════════════════════
# Result Rendering (Elite Chat-First Experience)
# ═══════════════════════════════════════════════════════════════════════════

res = st.session_state.last_result

if res:
    # 1. User Bubble
    st.markdown(f'<div class="chat-bubble-user">{res["q"]}</div>', unsafe_allow_html=True)
    
    # 2. AI Response Card
    with st.container():
        st.markdown('<div class="chat-container-ai">', unsafe_allow_html=True)
        
        # Handle Errors nicely
        if res.get("error") and not res.get("df") is not None:
            st.error(f"🛑 {res['error']}")
            if res.get("sql"):
                with st.expander("View generated SQL"):
                    st.code(res["sql"], language="sql")
            st.markdown('</div>', unsafe_allow_html=True)
            st.stop()
            
        # Empty Data State
        if res.get("empty"):
            st.info("📭 **No results found.** Try refining your question or adjusting your filters.")
            st.markdown('</div>', unsafe_allow_html=True)
            st.stop()

        # Data Exists -> Render Hierarchy
        df = res["df"]
        
        # SECTION 1: INSIGHT (Top priority)
        if res.get("insight"):
            icon = "⚠️" if res.get("fallback") else "💡"
            st.markdown(f'''
            <div class="insight-block">
                <span class="insight-icon">{icon}</span>
                <div>{res["insight"]}</div>
            </div>
            ''', unsafe_allow_html=True)
            
        # SECTION 2: CHART
        if res.get("chart"):
            st.plotly_chart(res["chart"], use_container_width=True, config={'displayModeBar': False})
            st.markdown("<br>", unsafe_allow_html=True)
            
        # SECTION 3 & 4: DATA and SQL
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander(f"📄 Data Table ({len(df)} rows)"):
                st.caption("Showing top 50 rows")
                st.dataframe(df.head(50), use_container_width=True, hide_index=True)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Full CSV",
                    data=csv,
                    file_name="askdatasage_export.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
        with col2:
            show_sql_default = st.session_state.ui_settings.get("show_sql", False)
            with st.expander("🧾 SQL Query", expanded=show_sql_default):
                st.code(res["sql"], language="sql")
                if res.get("explanation"):
                    st.caption(f"**Explanation:** {res['explanation']}")
                st.caption(f"⏱️ Execution time: {res.get('time', 0)}s")

        st.markdown('</div>', unsafe_allow_html=True)

else:
    # ═══════════════════════════════════════════════════════════════════════════
    # Empty State (When no query is run yet)
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class="empty-state-card">
        <h2 style="font-weight: 600; color: #E2E8F0; margin-bottom: 0.5rem;">Ask anything about your data</h2>
        <p style="color: #94A3B8; font-size: 1.1rem; margin-bottom: 2rem;">Type your question below or try one of the quick suggestions in the sidebar.</p>
        <span style="font-size: 3rem; filter: drop-shadow(0 0 10px rgba(108,99,255,0.4));">✨</span>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown('<div class="footer">Built with AI • AskDataSage</div>', unsafe_allow_html=True)