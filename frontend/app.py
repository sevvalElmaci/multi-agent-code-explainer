import streamlit as st
import requests
import re
import base64
from pathlib import Path

API_URL = "http://localhost:8000/api/v1/ask"

st.set_page_config(
    page_title="FastAPI Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------- LOGO ----------
def add_logo():
    logo_path = Path(__file__).parent / "assets" / "company_logo.jpg"

    if not logo_path.exists():
        return  # logo yoksa patlamasın

    encoded = base64.b64encode(logo_path.read_bytes()).decode()

    st.markdown(
        f"""
        <style>
        .logo-container {{
            position: fixed;
            top: 15px;
            right: 25px;
            z-index: 999;
        }}
        </style>

        <div class="logo-container">
            <img src="data:image/jpeg;base64,{encoded}" width="80"/>
        </div>
        """,
        unsafe_allow_html=True
    )

add_logo()

# ---------- CSS ----------
st.markdown("""
<style>
    .stApp { background-color: #0f1117; }

    .hero {
        background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
        border: 1px solid #2d3561;
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    .hero h1 { color: #e2e8f0; font-size: 2rem; margin: 0; }
    .hero p  { color: #94a3b8; margin: 0.5rem 0 0; font-size: 1rem; }

    .card {
        background: #1e2130;
        border: 1px solid #2d3561;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
    }
    .card-title {
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .accent-blue   { color: #60a5fa; }
    .accent-green  { color: #34d399; }
    .accent-purple { color: #a78bfa; }
    .accent-yellow { color: #fbbf24; }
    .accent-pink   { color: #f472b6; }

    .lbl-item {
        background: #252a3d;
        border-left: 3px solid #3b82f6;
        border-radius: 0 8px 8px 0;
        padding: 0.6rem 1rem;
        margin-bottom: 0.5rem;
        color: #cbd5e1;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    .bp-item {
        background: #252a3d;
        border-left: 3px solid #10b981;
        border-radius: 0 8px 8px 0;
        padding: 0.6rem 1rem;
        margin-bottom: 0.5rem;
        color: #cbd5e1;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    .source-link {
        display: block;
        background: #252a3d;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        margin-bottom: 0.4rem;
        color: #93c5fd !important;
        font-size: 0.82rem;
        text-decoration: none;
        word-break: break-all;
    }
    .source-link:hover { border-color: #3b82f6; }

    .meta-badge {
        display: inline-block;
        background: #2d3561;
        color: #a5b4fc;
        border-radius: 20px;
        padding: 0.25rem 0.9rem;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stTextArea textarea {
        background: #1e2130 !important;
        border: 1px solid #2d3561 !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-size: 1rem !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 2.5rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        transition: opacity 0.2s !important;
    }
    .stButton > button:hover { opacity: 0.88 !important; }

    hr { border-color: #2d3561 !important; }

    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---------- HELPERS ----------
def strip_code_fences(code: str) -> str:
    code = (code or "").strip()
    code = code.replace("\\n", "\n")
    code = re.sub(r"^```[a-zA-Z]*\n?", "", code)
    code = re.sub(r"\n?```$", "", code)
    code = re.sub(r',\s*["\']python code as a string["\']', "", code)
    code = re.sub(r'["\']python code as a string["\']', "", code)
    code = code.strip().strip('"').strip("'").strip()
    return code

# ---------- HEADER ----------
st.markdown("""
<div class="hero">
    <h1>⚡ FastAPI Expert Assistant</h1>
    <p>Learn FastAPI core topics with official docs (RAG) + real GitHub examples + line-by-line explanations.</p>
    <p style="margin-top:0.6rem; color:#64748b; font-size:0.95rem;">
        Topics: REST API · WebSocket · Auth (OAuth2/JWT) · Dependencies · Middleware · Background Tasks · Testing · Deployment
    </p>
</div>
""", unsafe_allow_html=True)


# ---------- INPUT ----------
col_input, col_btn = st.columns([5, 1])
with col_input:
    query = st.text_area(
        label="Soru",
        label_visibility="collapsed",
        height=100,
        placeholder="Ask a FastAPI question… e.g., 'How do Dependencies work?' or 'OAuth2 JWT flow in FastAPI?'",
    )
with col_btn:
    st.write("")
    st.write("")
    submit = st.button("🚀 Ask")

# ---------- MAIN ----------
if submit:
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Working… Query Analyzer → FastAPI Docs (RAG) → GitHub Example Finder → Code Explainer"):
            try:
                r = requests.post(API_URL, json={"query": query}, timeout=480)
                r.raise_for_status()
                data = r.json()
            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to the API. Is `uvicorn app.main:app --reload` running?")
                st.stop()
            except requests.exceptions.Timeout:
                st.error("❌ The request timed out. The model might be busy, please try again.")
                st.stop()
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.stop()

        meta = data.get("meta") or {}
        fw    = meta.get("framework", "unknown")
        topic = meta.get("topic", "unknown")

        st.markdown(f"""
        <div style="margin-bottom:1.2rem">
            <span class="meta-badge">⚙️ {fw}</span>
            <span class="meta-badge">📌 {topic}</span>
        </div>
        """, unsafe_allow_html=True)

        left, right = st.columns([3, 2])

        with left:
            st.markdown('<div class="card"><div class="card-title accent-blue">📖 Explanation</div>', unsafe_allow_html=True)
            st.markdown(data.get("explanation", ""), unsafe_allow_html=False)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card"><div class="card-title accent-purple">💻 Code Example</div>', unsafe_allow_html=True)
            clean_code = strip_code_fences(data.get("code_example", ""))
            if clean_code:
                st.code(clean_code, language="python")
            else:
                st.info("No code example found.")
            st.markdown('</div>', unsafe_allow_html=True)

        with right:
            lbl = data.get("line_by_line", [])
            if lbl:
                st.markdown('<div class="card"><div class="card-title accent-yellow">🔍 Line by Line</div>', unsafe_allow_html=True)
                for item in lbl:
                    st.markdown(f'<div class="lbl-item">• {item}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            bp = data.get("best_practices", [])
            if bp:
                st.markdown('<div class="card"><div class="card-title accent-green">✅ Best Practices</div>', unsafe_allow_html=True)
                for item in bp:
                    st.markdown(f'<div class="bp-item">✓ {item}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            sources = data.get("sources", [])
            if sources:
                st.markdown('<div class="card"><div class="card-title accent-pink">🔗 Sources</div>', unsafe_allow_html=True)
                for s in sources:
                    if s.startswith("http"):
                        domain = s.split("/")[2]
                        st.markdown(f'<a class="source-link" href="{s}" target="_blank">🔗 {domain}</a>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="source-link">📄 {s}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
