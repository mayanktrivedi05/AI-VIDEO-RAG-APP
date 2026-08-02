import streamlit as st
import time
import os
import json

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from datetime import datetime
from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.sammarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

# ─── Page Configuration (MUST BE FIRST STREAMLIT COMMAND) ──────────────────────
st.set_page_config(
    page_title="VideoRAG Pro • AI Meeting & Video Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sync Streamlit Cloud Secrets to os.environ
try:
    for k, v in st.secrets.items():
        if isinstance(v, str):
            os.environ[k] = v
except Exception:
    pass

# ─── Custom Cyber-Glass CSS Styling ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Color Tokens & Variables ── */
:root {
    --bg-dark: #07090e;
    --surface-1: #0e111a;
    --surface-2: #161b29;
    --surface-3: #1f2639;
    --border-color: rgba(255, 255, 255, 0.08);
    --border-glow: rgba(139, 92, 246, 0.3);
    
    --primary: #8b5cf6;
    --primary-glow: #a78bfa;
    --accent-cyan: #06b6d4;
    --accent-pink: #ec4899;
    --accent-green: #10b981;
    --accent-amber: #f59e0b;
    
    --text-primary: #f3f4f6;
    --text-secondary: #9ca3af;
    --text-muted: #6b7280;
}

/* ── Reset & Global Styles ── */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: var(--bg-dark) !important;
    color: var(--text-primary) !important;
}

.stApp {
    background: radial-gradient(circle at 50% 0%, #15102a 0%, #07090e 70%) !important;
    background-attachment: fixed !important;
}

/* Background Grid FX */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    background-image: 
        radial-gradient(rgba(139, 92, 246, 0.12) 1px, transparent 0);
    background-size: 32px 32px;
    pointer-events: none;
    z-index: 0;
}

/* ── Hide Header & Footer Defaults ── */
header[data-testid="stHeader"] {
    background: transparent !important;
}
footer { visibility: hidden; }

/* ── Sidebar Customization ── */
[data-testid="stSidebar"] {
    background: rgba(14, 17, 26, 0.85) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid var(--border-color) !important;
}

[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}

/* ── Typography & Headings ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

.brand-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0 20px 0;
}

.brand-icon {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, var(--primary), var(--accent-pink));
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.4);
}

.brand-title {
    font-size: 1.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ffffff 30%, var(--primary-glow) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.1;
}

.brand-sub {
    font-size: 0.72rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.15em;
    font-weight: 600;
}

/* ── Glass Cards & Containers ── */
.glass-card {
    background: rgba(22, 27, 41, 0.65);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.glass-card:hover {
    border-color: var(--border-glow);
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35), 0 0 15px rgba(139, 92, 246, 0.15);
}

.glass-card-accent {
    border-top: 3px solid var(--primary);
}

.glass-card-cyan {
    border-top: 3px solid var(--accent-cyan);
}

.glass-card-green {
    border-top: 3px solid var(--accent-green);
}

.glass-card-amber {
    border-top: 3px solid var(--accent-amber);
}

.card-header-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--primary-glow);
    background: rgba(139, 92, 246, 0.12);
    border: 1px solid rgba(139, 92, 246, 0.25);
    padding: 4px 10px;
    border-radius: 20px;
    margin-bottom: 12px;
}

.card-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.card-body {
    font-size: 0.92rem;
    line-height: 1.7;
    color: var(--text-primary);
}

/* ── Metric Display Boxes ── */
.metric-box {
    background: rgba(14, 17, 26, 0.7);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ffffff, var(--primary-glow));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-top: 4px;
}

/* ── Custom Badges ── */
.badge-pill {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 6px;
    margin-bottom: 6px;
}

.badge-purple { background: rgba(139, 92, 246, 0.2); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.4); }
.badge-cyan   { background: rgba(6, 182, 212, 0.2);  color: #67e8f9; border: 1px solid rgba(6, 182, 212, 0.4); }
.badge-green  { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }
.badge-amber  { background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.4); }

/* ── Custom Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, var(--primary) 0%, #6d28d9 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.03em !important;
    padding: 10px 24px !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.5) !important;
    background: linear-gradient(135deg, #a78bfa 0%, var(--primary) 100%) !important;
}

/* Secondary Buttons */
.stButton > button[kind="secondary"] {
    background: rgba(31, 38, 57, 0.8) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    box-shadow: none !important;
}

.stButton > button[kind="secondary"]:hover {
    background: rgba(45, 55, 82, 1) !important;
    border-color: var(--primary) !important;
}

/* ── Inputs & Selects ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: rgba(14, 17, 26, 0.8) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-size: 0.9rem !important;
    padding: 10px 14px !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.25) !important;
}

/* ── Custom Code / Pre Boxes ── */
.code-box {
    background: rgba(10, 12, 18, 0.9);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: #d1d5db;
    max-height: 400px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Custom Scrollbars ── */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: rgba(7, 9, 14, 0.5);
}
::-webkit-scrollbar-thumb {
    background: rgba(139, 92, 246, 0.4);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: var(--primary);
}

/* ── Streamlit Tabs Overrides ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(14, 17, 26, 0.6);
    padding: 6px;
    border-radius: 14px;
    border: 1px solid var(--border-color);
}

.stTabs [data-baseweb="tab"] {
    height: 44px;
    white-space: pre;
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.88rem;
    color: var(--text-secondary);
    border: none !important;
    background-color: transparent;
    padding: 0px 20px;
    transition: all 0.2s ease;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(109, 40, 217, 0.3) 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(139, 92, 246, 0.5) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

/* ── Pulse Status Indicator ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    background: rgba(22, 27, 41, 0.8);
    border: 1px solid var(--border-color);
    font-size: 0.8rem;
    font-weight: 600;
}

.pulse-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
}
.pulse-green { background: var(--accent-green); box-shadow: 0 0 10px var(--accent-green); }
.pulse-purple { background: var(--primary); box-shadow: 0 0 10px var(--primary); animation: pulse-anim 1.5s infinite; }
.pulse-amber { background: var(--accent-amber); box-shadow: 0 0 10px var(--accent-amber); }

@keyframes pulse-anim {
    0% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.85); }
    100% { opacity: 1; transform: scale(1); }
}
</style>
""", unsafe_allow_html=True)

# ─── Initialize Session State ────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running = False
if "pipeline_steps" not in st.session_state:
    st.session_state.pipeline_steps = {}

# ─── Sidebar Content ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="brand-header">
        <div class="brand-icon">⚡</div>
        <div>
            <div class="brand-title">VideoRAG Pro</div>
            <div class="brand-sub">AI Video Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown("### 📥 Input Source")
    
    input_tab = st.radio(
        "Source Type",
        ["🔗 YouTube URL", "📁 Upload File", "💻 Local Path"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    source = ""
    if input_tab == "🔗 YouTube URL":
        source = st.text_input(
            "YouTube Video URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Enter any valid YouTube video link"
        )
    elif input_tab == "📁 Upload File":
        uploaded_file = st.file_uploader(
            "Upload Video / Audio",
            type=["mp4", "mov", "avi", "mp3", "wav", "m4a"],
            help="Upload meeting recording or audio file"
        )
        if uploaded_file is not None:
            os.makedirs("downloades", exist_ok=True)
            save_path = os.path.join("downloades", uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            source = save_path
            st.success(f"Loaded: `{uploaded_file.name}`")
    else:
        source = st.text_input(
            "Local File Path",
            placeholder="/Users/username/Videos/meeting.mp4",
            help="Enter absolute path to local video/audio file"
        )
    
    st.markdown("---")
    st.markdown("### ⚙️ Engine Settings")
    
    language = st.selectbox(
        "Transcription Language",
        ["english", "hinglish"],
        index=0,
        help="English uses Whisper. Hinglish uses Sarvam AI with automatic English translation."
    )
    
    if language == "hinglish":
        st.caption("ℹ️ Using **Sarvam AI (Saaras v2.5)** for Indian accents & Hinglish speech.")
    else:
        st.caption("ℹ️ Using **OpenAI Whisper** for high-accuracy English transcription.")

    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
    
    run_btn = st.button("🚀 Process & Analyze", use_container_width=True)

    # Sidebar Pipeline Status Card (if processed)
    if st.session_state.result is not None:
        st.markdown("---")
        st.markdown("### 📊 Active Pipeline Stats")
        r_meta = st.session_state.result.get("metadata", {})
        
        st.markdown(f"""
        <div style="font-size:0.82rem; color:var(--text-secondary); line-height:1.8;">
            <div>⏱️ <b>Processed at:</b> {r_meta.get('timestamp', 'N/A')}</div>
            <div>🔊 <b>Audio Chunks:</b> {r_meta.get('chunk_count', 1)}</div>
            <div>⚡ <b>Language Mode:</b> <span class="badge-pill badge-purple">{language.upper()}</span></div>
            <div>🧠 <b>RAG Index:</b> <span class="badge-pill badge-green">ACTIVE</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        
        # Export options
        summary_md = f"# {st.session_state.result['title']}\n\n## Summary\n{st.session_state.result['summary']}\n\n## Action Items\n{st.session_state.result['action_items']}\n\n## Key Decisions\n{st.session_state.result['key_decisions']}\n\n## Open Questions\n{st.session_state.result['open_questions']}"
        st.download_button(
            "📥 Export Executive Report (.md)",
            data=summary_md,
            file_name=f"Executive_Report_{int(time.time())}.md",
            mime="text/markdown",
            use_container_width=True
        )
        st.download_button(
            "📜 Download Full Transcript (.txt)",
            data=st.session_state.result.get('transcript', ''),
            file_name=f"Transcript_{int(time.time())}.txt",
            mime="text/plain",
            use_container_width=True
        )
        if st.button("🔄 Analyze Another Video", type="secondary", use_container_width=True):
            st.session_state.result = None
            st.session_state.chat_history = []
            st.rerun()

# ─── Main Content Area ───────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
    <div>
        <h1 style="margin:0; font-size:2.2rem;">🎬 Meeting & Video RAG Intelligence</h1>
        <p style="color:var(--text-secondary); margin:4px 0 0 0; font-size:0.95rem;">
            Turn long videos and meetings into actionable summaries, key decisions, and live interactive Q&A.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Process Execution Pipeline ──────────────────────────────────────────────────
if run_btn:
    if not source.strip():
        st.error("⚠️ Please specify a valid YouTube URL, upload a file, or enter a file path.")
    else:
        st.session_state.pipeline_running = True
        st.session_state.result = None
        st.session_state.chat_history = []
        
        progress_box = st.empty()
        start_time = time.time()
        
        try:
            with progress_box.container():
                st.markdown("""
                <div class="glass-card glass-card-accent">
                    <div class="card-header-badge">⚡ Pipeline Running</div>
                    <div class="card-title">Processing Video & Extracting Intelligence...</div>
                    <p style="color:var(--text-secondary); font-size:0.88rem;">
                        Extracting audio, transcribing, indexing vector store, and running multi-task LLM chains.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.spinner("1/5 🔊 Downloading & Chunking Audio..."):
                    chunks = process_input(source)
                
                with st.spinner("2/5 📝 Transcribing Speech to Text..."):
                    transcript = transcribe_all(chunks, language)
                
                with st.spinner("3/5 🏷️ Generating Executive Title & Summary..."):
                    title = generate_title(transcript)
                    summary = summarize(transcript)
                
                with st.spinner("4/5 🔍 Extracting Action Items, Decisions & Questions..."):
                    action_items = extract_action_items(transcript)
                    decisions = extract_key_decisions(transcript)
                    questions = extract_questions(transcript)
                
                with st.spinner("5/5 🧠 Indexing Vectors & Initializing RAG Engine..."):
                    rag_chain = build_rag_chain(transcript)

            elapsed_time = round(time.time() - start_time, 2)
            
            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
                "metadata": {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "chunk_count": len(chunks),
                    "execution_time": f"{elapsed_time}s",
                    "word_count": len(transcript.split()),
                }
            }
            st.session_state.pipeline_running = False
            progress_box.empty()
            st.toast("🎉 Analysis completed successfully!", icon="✅")
            st.rerun()

        except Exception as e:
            st.session_state.pipeline_running = False
            progress_box.error(f"❌ Error during processing: {str(e)}")

# ─── Results Dashboard View ──────────────────────────────────────────────────────
if st.session_state.result is not None:
    res = st.session_state.result
    meta = res.get("metadata", {})
    
    # Hero Title Card
    st.markdown(f"""
    <div class="glass-card glass-card-accent">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
            <div>
                <div class="card-header-badge">📌 Executive Video Analysis</div>
                <div style="font-size:1.6rem; font-weight:800; color:#ffffff; line-height:1.2;">
                    {res['title']}
                </div>
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
                <span class="badge-pill badge-purple">📝 {meta.get('word_count', 0)} Words</span>
                <span class="badge-pill badge-cyan">⚡ {meta.get('execution_time', '0s')} Runtime</span>
                <span class="badge-pill badge-green">🧠 RAG Ready</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Multi-Tab Interface
    tab_overview, tab_chat, tab_transcript, tab_tech = st.tabs([
        "📊 Overview & Insights",
        "💬 Ask Assistant (RAG Chat)",
        "📜 Full Transcript",
        "⚙️ RAG Engine Stats"
    ])
    
    # TAB 1: OVERVIEW & INSIGHTS
    with tab_overview:
        # Metrics Top Row
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            st.markdown("""
            <div class="metric-box">
                <div class="metric-value">📋</div>
                <div class="metric-label">Executive Summary</div>
            </div>
            """, unsafe_allow_html=True)
        with mcol2:
            st.markdown("""
            <div class="metric-box">
                <div class="metric-value">✅</div>
                <div class="metric-label">Action Items</div>
            </div>
            """, unsafe_allow_html=True)
        with mcol3:
            st.markdown("""
            <div class="metric-box">
                <div class="metric-value">🔑</div>
                <div class="metric-label">Key Decisions</div>
            </div>
            """, unsafe_allow_html=True)
        with mcol4:
            st.markdown("""
            <div class="metric-box">
                <div class="metric-value">❓</div>
                <div class="metric-label">Open Questions</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        
        # Summary Card
        st.markdown("""
        <div class="glass-card glass-card-cyan">
            <div class="card-title">📋 Executive Summary</div>
            <div class="card-body">
        """, unsafe_allow_html=True)
        st.markdown(res['summary'])
        st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Insights Grid
        col_act, col_dec, col_q = st.columns(3)
        
        with col_act:
            st.markdown("""
            <div class="glass-card glass-card-green" style="height:100%;">
                <div class="card-title">✅ Action Items</div>
                <div class="card-body">
            """, unsafe_allow_html=True)
            st.markdown(res['action_items'])
            st.markdown("</div></div>", unsafe_allow_html=True)
            
        with col_dec:
            st.markdown("""
            <div class="glass-card glass-card-accent" style="height:100%;">
                <div class="card-title">🔑 Key Decisions</div>
                <div class="card-body">
            """, unsafe_allow_html=True)
            st.markdown(res['key_decisions'])
            st.markdown("</div></div>", unsafe_allow_html=True)
            
        with col_q:
            st.markdown("""
            <div class="glass-card glass-card-amber" style="height:100%;">
                <div class="card-title">❓ Open Questions</div>
                <div class="card-body">
            """, unsafe_allow_html=True)
            st.markdown(res['open_questions'])
            st.markdown("</div></div>", unsafe_allow_html=True)

    # TAB 2: RAG INTERACTIVE CHAT
    with tab_chat:
        st.markdown("""
        <div class="glass-card glass-card-accent" style="margin-bottom:15px;">
            <div class="card-title">💬 Interactive Transcript RAG Chat</div>
            <div style="font-size:0.85rem; color:var(--text-secondary);">
                Ask anything about the video content. Answers are retrieved grounded directly in the transcript using vector similarity.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick Question Suggestions
        st.markdown("##### 💡 Suggested Questions")
        q_cols = st.columns(3)
        suggested_q = None
        with q_cols[0]:
            if st.button("📌 What were the main topics discussed?", use_container_width=True, type="secondary"):
                suggested_q = "What were the main topics discussed?"
        with q_cols[1]:
            if st.button("👥 Who is responsible for action items?", use_container_width=True, type="secondary"):
                suggested_q = "Who is responsible for action items?"
        with q_cols[2]:
            if st.button("🚀 What are the next immediate steps?", use_container_width=True, type="secondary"):
                suggested_q = "What are the next immediate steps?"

        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

        # Display Existing Chat History
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        # Chat Input Bar
        user_input = st.chat_input("Ask a question about this video/meeting transcript...")
        query = user_input or suggested_q
        
        if query:
            st.session_state.chat_history.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)
                
            with st.chat_message("assistant"):
                with st.spinner("🧠 Querying Vector Store & Mistral AI..."):
                    answer = ask_question(res["rag_chain"], query)
                    st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

        if st.session_state.chat_history:
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            if st.button("🗑️ Clear Chat History", type="secondary"):
                st.session_state.chat_history = []
                st.rerun()

    # TAB 3: FULL TRANSCRIPT
    with tab_transcript:
        st.markdown("""
        <div class="glass-card glass-card-cyan">
            <div class="card-title">📜 Full Video Transcript</div>
            <div style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:15px;">
                Complete transcript generated via speech-to-text model.
            </div>
        """, unsafe_allow_html=True)
        
        search_kw = st.text_input("🔍 Search Keyword in Transcript", placeholder="Type keyword to filter...")
        
        transcript_text = res["transcript"]
        if search_kw.strip():
            lines = transcript_text.split(".")
            matching = [l.strip() for l in lines if search_kw.lower() in l.lower()]
            if matching:
                st.info(f"Found {len(matching)} matching sentence(s):")
                for m in matching:
                    st.markdown(f"- ...{m}...")
            else:
                st.warning("No matching sentences found.")
            st.markdown("---")
            
        st.markdown(f'<div class="code-box">{transcript_text}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.download_button(
            "📥 Download Full Transcript (.txt)",
            data=transcript_text,
            file_name=f"transcript_{int(time.time())}.txt",
            mime="text/plain"
        )

    # TAB 4: RAG ENGINE STATS
    with tab_tech:
        st.markdown("""
        <div class="glass-card glass-card-accent">
            <div class="card-title">⚙️ RAG Engine & Architecture Specifications</div>
            <div class="card-body">
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:16px;">
                    <div style="background:rgba(14,17,26,0.8); padding:14px; border-radius:10px; border:1px solid var(--border-color);">
                        <div style="font-size:0.75rem; color:var(--text-secondary); text-transform:uppercase;">LLM Model</div>
                        <div style="font-size:1.1rem; font-weight:700; color:var(--primary-glow); margin-top:4px;">Mistral Small Latest</div>
                    </div>
                    <div style="background:rgba(14,17,26,0.8); padding:14px; border-radius:10px; border:1px solid var(--border-color);">
                        <div style="font-size:0.75rem; color:var(--text-secondary); text-transform:uppercase;">Vector Embeddings</div>
                        <div style="font-size:1.1rem; font-weight:700; color:var(--accent-cyan); margin-top:4px;">Mistral Embeddings</div>
                    </div>
                    <div style="background:rgba(14,17,26,0.8); padding:14px; border-radius:10px; border:1px solid var(--border-color);">
                        <div style="font-size:0.75rem; color:var(--text-secondary); text-transform:uppercase;">STT Engine</div>
                        <div style="font-size:1.1rem; font-weight:700; color:var(--accent-green); margin-top:4px;">Whisper / Sarvam AI</div>
                    </div>
                    <div style="background:rgba(14,17,26,0.8); padding:14px; border-radius:10px; border:1px solid var(--border-color);">
                        <div style="font-size:0.75rem; color:var(--text-secondary); text-transform:uppercase;">Vector Store</div>
                        <div style="font-size:1.1rem; font-weight:700; color:var(--accent-amber); margin-top:4px;">FAISS / In-Memory</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ─── Empty Initial State ─────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px;" class="glass-card">
        <div style="font-size: 4rem; margin-bottom: 15px;">⚡</div>
        <h2 style="font-size: 1.8rem; margin-bottom: 10px;">Ready to Extract Video Intelligence</h2>
        <p style="color: var(--text-secondary); max-width: 550px; margin: 0 auto 25px auto; font-size: 0.95rem; line-height: 1.6;">
            Select a input source from the sidebar (YouTube URL, direct video upload, or local file), pick your language model, and click <strong>Process & Analyze</strong>.
        </p>
        <div style="display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;">
            <span class="badge-pill badge-purple">✨ Automatic Transcription</span>
            <span class="badge-pill badge-cyan">📋 AI Summarization</span>
            <span class="badge-pill badge-green">✅ Action Item Extraction</span>
            <span class="badge-pill badge-amber">💬 RAG Conversational AI</span>
        </div>
    </div>
    """, unsafe_allow_html=True)