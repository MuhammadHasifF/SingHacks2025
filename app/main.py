import streamlit as st
import requests
import uuid
import json
from pathlib import Path
from components.upload_panel import render_upload_panel

# ===========================
# Config
# ===========================
API_BASE = "http://127.0.0.1:8000"
CHAT_URL = f"{API_BASE}/chat"

st.set_page_config(page_title="Your Travel Assistant", page_icon="💬", layout="wide")
st.title("Your Travel Assistant")

# ===========================
# Tiny on-disk session store (for chat persistence)
# ===========================
SESS_DIR = Path(".sessions")
SESS_DIR.mkdir(exist_ok=True)

def _session_file(sid: str) -> Path:
    return SESS_DIR / f"{sid}.json"

def load_messages(sid: str) -> list[dict]:
    p = _session_file(sid)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_messages(sid: str, messages: list[dict]) -> None:
    _session_file(sid).write_text(json.dumps(messages, ensure_ascii=False), encoding="utf-8")

# ===========================
# 🔑 Session bootstrap FIRST (before sidebar!)
# ===========================
# Make SID sticky in URL so both chat + upload panel share the same ID.
params = dict(st.query_params)
sid = params.get("sid")
if not sid:
    sid = f"user_{uuid.uuid4().hex[:8]}"
    st.query_params = {**params, "sid": sid}

# Put sid + messages into session_state
st.session_state.setdefault("session_id", sid)
if "messages" not in st.session_state:
    st.session_state.messages = load_messages(st.session_state.session_id)

# ===========================
# Sidebar — Upload Panel (now it sees the correct session_id)
# ===========================
with st.sidebar:
    st.header("📎 Upload Travel Document")
    st.caption("Upload your ticket or itinerary (PDF or image). We'll summarize and suggest the best plan.")
    render_upload_panel(API_BASE)  # now gets the real SID from session_state

# ===========================
# Toolbar
# ===========================
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("New chat"):
        new_sid = f"user_{uuid.uuid4().hex[:8]}"
        st.session_state.session_id = new_sid
        st.session_state.messages = []
        st.query_params = {**st.query_params, "sid": new_sid}
        st.rerun()

# ===========================
# Chat Section
# ===========================
st.subheader("Chat with your Personal Travel Assistant!")
st.caption("Ask questions like *Which plan has better coverage?* or *Am I covered for skiing in Japan?*")

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# Chat input + call backend
if prompt := st.chat_input("Ask about trip cancellation, medical coverage, eligibility…"):
    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_messages(st.session_state.session_id, st.session_state.messages)
    with st.chat_message("user"):
        st.markdown(prompt)

    # Backend call
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    CHAT_URL,
                    json={"question": prompt, "session_id": st.session_state.session_id},
                    timeout=120,
                )

                if resp.status_code != 200:
                    st.error(f"Server error {resp.status_code}")
                    st.code(resp.text)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": f"Server error {resp.status_code}:\n{resp.text}"}
                    )
                    save_messages(st.session_state.session_id, st.session_state.messages)
                else:
                    text = resp.text or "No response."
                    try:
                        data = resp.json()
                        text = data.get("text") or data.get("message") or text
                        if data.get("intent") == "error":
                            st.error(text)
                            meta = data.get("meta") or {}
                            detail = meta.get("error") or meta.get("detail")
                            if detail:
                                st.code(detail)
                                text = f"{text}\n\n```text\n{detail}\n```"
                    except Exception:
                        pass

                    st.markdown(text, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": text})
                    save_messages(st.session_state.session_id, st.session_state.messages)

            except requests.exceptions.Timeout:
                msg = "Timeout while contacting the API."
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
                save_messages(st.session_state.session_id, st.session_state.messages)
            except Exception as e:
                msg = f"API error: {e}"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
                save_messages(st.session_state.session_id, st.session_state.messages)
