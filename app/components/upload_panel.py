import streamlit as st
import requests

def render_upload_panel(api_url: str):
    st.subheader("📎 Upload a Travel Document")
    st.caption("Upload a PDF or image. (Saved locally for now — database coming soon.)")

    file = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg", "webp"])
    if file:
        with st.spinner("Uploading..."):
            files = {"file": (file.name, file, file.type)}
            resp = requests.post(f"{api_url}/upload", files=files)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    st.success(f"✅ Uploaded `{data['filename']}` successfully!")
                    st.code(data["path"])
                else:
                    st.error(f"Upload failed: {data.get('error', 'Unknown error')}")
            else:
                st.error(f"Server error: {resp.status_code}")
