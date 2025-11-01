import streamlit as st
import requests
import uuid
from components.upload_panel import render_upload_panel

# ===========================
# Config
# ===========================
API_BASE = "http://127.0.0.1:8000"
CHAT_URL = f"{API_BASE}/chat"

st.set_page_config(page_title="Insurance Scammer 🧳", page_icon="💬", layout="wide")
st.title("🧳 Insurance Scammer — MSIG x Scootsurance Assistant")

# ===========================
# Sidebar — Upload Panel
# ===========================
with st.sidebar:
    st.header("📎 Upload Travel Document")
    st.caption("Upload your ticket or itinerary (PDF or image). We'll summarize and suggest the best plan.")
    render_upload_panel(API_BASE)

# ===========================
# Session bootstrap
# ===========================
if "session_id" not in st.session_state:
    st.session_state.session_id = f"user_{uuid.uuid4().hex[:8]}"
if "messages" not in st.session_state:
    st.session_state.messages = []

# ===========================
# Chat Section
# ===========================
st.subheader("💬 Chat with Insurance Scammer")
st.caption("Ask questions like *Which plan has better coverage?* or *Am I covered for skiing in Japan?*")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Ask about trip cancellation, medical coverage, eligibility…"):
    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Backend call
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    CHAT_URL,
                    json={"question": prompt, "session_id": st.session_state.session_id},
                    timeout=60,
                )
                data = resp.json()
                text = data.get("text", "No response.")
                st.markdown(text, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": text})
            except Exception as e:
                err = f"API error: {e}"
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})
