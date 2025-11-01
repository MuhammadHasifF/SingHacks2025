import streamlit as st
import requests
import uuid

API_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(page_title="Insurance Scammer 🧳", page_icon="💬")
st.title("🧳 Insurance Scammer")

# Session bootstrap
if "session_id" not in st.session_state:
    st.session_state.session_id = f"user_{uuid.uuid4().hex[:8]}"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # ✅ change write() → markdown() to render clickable links
        st.markdown(msg["content"], unsafe_allow_html=True)

# Input → call API → render
if prompt := st.chat_input("Ask about trip cancellation, medical coverage, eligibility…"):
    # user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # call backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    API_URL,
                    json={"question": prompt, "session_id": st.session_state.session_id},
                    timeout=60,
                )
                data = resp.json()
                text = data.get("text", "No response.")

                # ✅ render assistant message as markdown (clickable links)
                st.markdown(text, unsafe_allow_html=True)

                # store assistant message
                st.session_state.messages.append({"role": "assistant", "content": text})

            except Exception as e:
                err = f"API error: {e}"
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})
