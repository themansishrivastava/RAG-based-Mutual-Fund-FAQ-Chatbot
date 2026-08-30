"""Streamlit query surface. Calls the retrieval backend. No upload, admin, or document upload."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "retrieval"))

import setup_paths  # noqa: E402, F401
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from pipeline import answer  # noqa: E402

GROWW_GREEN = "#00B386"
EXAMPLES = [
    "What is the expense ratio of HDFC Large Cap?",
    "ELSS lock-in?",
    "Minimum SIP for HDFC Small Cap?",
]

st.set_page_config(
    page_title="HDFC Fund Facts",
    page_icon=" ",
    layout="centered",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

st.markdown(
    f"""
<style>
    .stApp {{ background: #f7f8fa; color: #191c27; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    .hero {{
        background: {GROWW_GREEN};
        color: #ffffff;
        padding: 1.1rem 1.15rem;
        border-radius: 10px;
        margin-bottom: 0.75rem;
    }}
    .hero h1 {{
        font-size: 1.55rem;
        margin: 0 0 0.35rem 0;
        color: #ffffff;
    }}
    .hero p {{ margin: 0; color: #ffffff; }}
    .note {{
        background: #ffffff;
        border-left: 4px solid {GROWW_GREEN};
        padding: 0.55rem 0.8rem;
        margin-bottom: 0.9rem;
        color: #191c27;
    }}
    .stButton > button {{
        background: #ffffff;
        color: #191c27;
        border: 1px solid #d7dde5;
        border-radius: 8px;
        text-align: left;
        white-space: normal;
        height: auto;
        padding: 0.65rem 0.8rem;
    }}
    .stButton > button:hover {{
        border-color: {GROWW_GREEN};
        color: {GROWW_GREEN};
    }}
    [data-testid="stChatMessage"],
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] li,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p {{
        color: #111111 !important;
    }}
    [data-testid="stChatMessage"] a {{
        color: #0a66c2 !important;
    }}
    [data-testid="stChatInput"] textarea {{
        color: #111111 !important;
    }}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>HDFC Fund Facts</h1>
      <p>Ask a factual question about five HDFC Direct Growth funds listed on Groww.</p>
    </div>
    <div class="note">Facts-only. No investment advice.</div>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None

for i, q in enumerate(EXAMPLES):
    if st.button(q, key=f"ex_{i}", use_container_width=True):
        st.session_state.pending = q

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

typed = st.chat_input("Ask a factual question about one of the five funds")
question = st.session_state.pending or typed
if st.session_state.pending:
    st.session_state.pending = None

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Looking up indexed Groww pages…"):
            result = answer(question, generate_llm=True)
        st.markdown(result["text"])
    st.session_state.messages.append({"role": "assistant", "content": result["text"]})
    st.rerun()
