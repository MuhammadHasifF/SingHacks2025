import streamlit as st
import requests
import uuid
import json
import base64
import io
from pathlib import Path
from components.upload_panel import render_upload_panel
from components.payment_widget import render_payment_page

# ===========================
# Config
# ===========================
API_BASE = "http://127.0.0.1:8000"
CHAT_URL = f"{API_BASE}/chat"

# ===========================
# MSIG styling (sidebar light, main unchanged; specific widgets)
# ===========================
MSIG_CSS = """
:root{
  --msig-red:#E4002B;
  --msig-navy:#1F2A5A;
  --msig-navy-light:#2A3A74;

  --panel-border:#E9ECF5;
  --panel-text:#111111;
  --panel-muted:#596075;
  --panel-subtle:#F6F7FB;
}

/* Keep MAIN background/theme default — no global overrides */

/* ===== Sidebar: white MSIG panel ===== */
[data-testid="stSidebar"]{
  background:#FFFFFF !important;
  color:var(--panel-text) !important;
}

/* Sidebar text (incl. uploader helper text) -> black */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stFileUploader"] *{
  color:var(--panel-text) !important;
}
[data-testid="stSidebar"] .stCaption{ color:var(--panel-muted) !important; }

/* Sidebar card wrapper we can opt into via .sb-card class */
.sb-card{
  background:#FFFFFF;
  border:1px solid var(--panel-border);
  border-radius:12px;
  padding:16px;
  margin:10px 0 14px 0;
  box-shadow:0 1px 2px rgba(0,0,0,.04);
}

/* Uploader dropzone */
[data-testid="stSidebar"] [data-testid="stFileUploader"] > section{
  border:2px dashed var(--panel-border) !important;
  background:var(--panel-subtle) !important;
  border-radius:16px !important;
}

/* Sidebar buttons -> force WHITE text (hit button and its children) */
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] .stButton > button *{
  color:#FFFFFF !important;
}
[data-testid="stSidebar"] .stButton > button{
  background:var(--msig-navy) !important;
  border:0 !important;
  border-radius:12px !important;
}

/* Remove file (secondary) -> red */
[data-testid="stSidebar"] [data-testid="baseButton-secondary"],
[data-testid="stSidebar"] button[kind="secondary"]{
  background:var(--msig-red) !important;
  color:#FFFFFF !important;
  border:0 !important;
  border-radius:12px !important;
}

/* Download + Browse files (Streamlit widgets) -> white text on navy */
[data-testid="stSidebar"] [data-testid="stDownloadButton"] button,
[data-testid="stSidebar"] [data-testid="stFileUploader"] button{
  background:var(--msig-navy) !important;
  color:#FFFFFF !important;
  border-radius:12px !important;
}

/* <-- Add THIS extra rule to catch the nested label span: */
[data-testid="stSidebar"] [data-testid="stDownloadButton"] button *{
  color: #FFFFFF !important;
}

/* File uploader remove/cancel button - make it RED and visible */
button[aria-label*="Remove"],
button[aria-label*="Remove"] *,
[data-testid="stFileUploader"] button[aria-label*="Remove"],
[data-testid="stFileUploader"] button[aria-label*="Remove"] *,
[data-testid="stFileUploader"] [role="button"]:has(svg[viewBox="0 0 16 16"]){
  background:var(--msig-red) !important;
  border-color:var(--msig-red) !important;
  color:#FFFFFF !important;
}

/* ===== MAIN: chat panels white with black text; BOT outlined red ===== */
[data-testid="stAppViewContainer"] .main [data-testid="stChatMessage"]{
  background:#FFFFFF !important;
  color:#111111 !important;
  border:2px solid var(--msig-navy) !important;
  border-radius:14px !important;
}
[data-testid="stAppViewContainer"] .main [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] *{
  color:#111111 !important;
}
[data-testid="stAppViewContainer"] .main [data-testid="stChatMessage"]:has([data-testid="assistant-avatar"]){
  border-color:var(--msig-red) !important; /* BOT: red outline */
}

/* MAIN 'New chat' -> red primary */
[data-testid="stAppViewContainer"] .main [data-testid="baseButton-primary"],
[data-testid="stAppViewContainer"] .main button[kind="primary"]{
  background:var(--msig-red) !important;
  color:#FFFFFF !important;
  border:0 !important;
  border-radius:12px !important;
  box-shadow:0 6px 14px rgba(228,0,43,.18);
}

/* Voice input styling */
[data-testid="stAudioInput"] {
  margin-top: 8px;
}

[data-testid="stAudioInput"] > div {
  height: 60px !important;
  padding: 8px !important;
}

[data-testid="stAudioInput"] p {
  display: none !important;
}
"""

st.set_page_config(page_title="MSIG Travel Assistant", layout="wide")
st.markdown(f"<style>{MSIG_CSS}</style>", unsafe_allow_html=True)

# ===========================
# Title block and intro guide
# ===========================
st.markdown(
    """
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
        <div style="width:10px;height:28px;background:#E4002B;border-radius:6px;"></div>
        <h1 style="margin:0;">MSIG Travel Assistant</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <p style='font-size:16px;color:#cccccc;margin-top:-8px;'>
        Compare plans, check eligibility, and get quick, personalized guidance.
    </p>
    """,
    unsafe_allow_html=True,
)

st.divider()

st.markdown(
    """
    **How to use the assistant**

    You can talk to me like a real travel advisor. I’ll adapt to your tone and situation — whether you’re unsure, in a rush, or ready to choose a plan.  
    Try starting with questions like:

    | Situation | Example prompt |
    |------------|----------------|
    | Unsure where to start | “I’m not sure which travel insurance I need.” |
    | In a rush | “My flight is tomorrow — which plan can I buy right now?” |
    | Health concerns | “I have asthma — am I still eligible for coverage?” |
    | Trip planning | “Compare MSIG TravelEasy and Scootsurance for a trip to Japan.” |
    | Confused about terms | “What does trip cancellation really mean?” |
    | Budget-focused | “Which plan gives good medical coverage but is affordable?” |
    | Decision-ready | “Tell me the best plan for my trip, and I’ll go with that.” |

    I can also help you:
    - Compare coverage between plans  
    - Explain specific policy terms  
    - Suggest the right plan for your travel type  
    - Check eligibility for pre-existing conditions  
    - Summarize uploaded travel documents  

    *(Tip: Be as natural or as specific as you like — I’ll adjust my tone automatically.)*
    """,
)


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
# Session bootstrap FIRST (before sidebar)
# ===========================
params = dict(st.query_params)
sid = params.get("sid")
if not sid:
  sid = f"user_{uuid.uuid4().hex[:8]}"
  st.query_params = {**params, "sid": sid}

# Always update session_id to match query params
st.session_state.session_id = sid
if "messages" not in st.session_state:
  st.session_state.messages = load_messages(st.session_state.session_id)

# ===========================
# Handle payment success/cancel redirects
# ===========================
if params.get("payment_success") == "true":
    st.success("🎉 Payment completed successfully! Your insurance policy is now active.")
    st.balloons()
    st.session_state["payment_confirmed"] = True
    # Clean up query params
    clean_params = dict(st.query_params)
    clean_params.pop("payment_success", None)
    clean_params.pop("session_id", None)  # Stripe session ID
    st.query_params = clean_params

if params.get("payment_cancelled") == "true":
    st.warning("⚠️ Payment was cancelled. You can try again when ready.")
    clean_params = dict(st.query_params)
    clean_params.pop("payment_cancelled", None)
    st.query_params = clean_params

# ===========================
# Route to payment page if requested
# ===========================
current_page = params.get("page", "main")
if current_page == "payment":
  render_payment_page(API_BASE)
  st.stop()  # Don't render the main chat interface

# ===========================
# Sidebar — Upload Panel
# ===========================
with st.sidebar:
  render_upload_panel(API_BASE)

# ===========================
# Toolbar
# ===========================
col1, col2 = st.columns([1, 3])
with col1:
  if st.button("New chat", type="primary"):
    new_sid = f"user_{uuid.uuid4().hex[:8]}"
    st.session_state.session_id = new_sid
    st.session_state.messages = []
    st.query_params = {**st.query_params, "sid": new_sid}
    st.rerun()

# ===========================
# Chat Section
# ===========================
st.subheader("Chat with MSIG Assistant")
st.caption("Ask things like Which plan has better coverage? or Am I covered for skiing in Japan?")

# Render history
for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
    st.markdown(msg["content"], unsafe_allow_html=True)

# Chat input
text_prompt = st.chat_input("Ask about trip cancellation, medical coverage, eligibility...")

# Process if we have input
if text_prompt:
  # User message
  st.session_state.messages.append({"role": "user", "content": text_prompt})
  save_messages(st.session_state.session_id, st.session_state.messages)
  with st.chat_message("user"):
    st.markdown(text_prompt)

  # Backend call
  with st.chat_message("assistant"):
    with st.spinner("Thinking..."):
      try:
        resp = requests.post(
          CHAT_URL,
          json={"question": text_prompt, "session_id": st.session_state.session_id},
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
