import streamlit as st
import requests
import uuid
from components.upload_panel import render_upload_panel

# ===========================
# Config
# ===========================
API_BASE = "http://127.0.0.1:8000"
CHAT_URL = f"{API_BASE}/chat"

st.set_page_config(page_title="Insurance Scammer 🧳", page_icon="💬")
st.title("🧳 Insurance Scammer")

# ===========================
# Sidebar — File Upload
# ===========================
with st.sidebar:
    st.header("📎 Document Upload")
    st.caption("Upload a PDF or image (stored locally in `data/uploads/`).")
    render_upload_panel(API_BASE)

# ===========================
# Session bootstrap
# ===========================
if "session_id" not in st.session_state:
    st.session_state.session_id = f"user_{uuid.uuid4().hex[:8]}"
if "messages" not in st.session_state:
    st.session_state.messages = []

# ===========================
# Display chat history
# ===========================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# ===========================
# Chat Input & Response
# ===========================
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

                # Assistant message (markdown supports links)
                st.markdown(text, unsafe_allow_html=True)

                # Store in chat history
                st.session_state.messages.append({"role": "assistant", "content": text})

            except Exception as e:
                err = f"API error: {e}"
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})
