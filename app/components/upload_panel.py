import streamlit as st
import requests


def _render_trip_summary(trip: dict):
    """Display extracted trip info."""
    with st.container(border=True):
        st.markdown("### 🧾 Trip Summary (Preview)")
        st.markdown(f"**Traveler:** {trip.get('traveler_name', '—')}")
        st.markdown(f"**Destination:** {trip.get('destination', '—')}")
        st.markdown(f"**Dates:** {trip.get('dates', '—')}")
        st.markdown(f"**Trip Cost:** ${trip.get('trip_cost', '—'):,}")


def render_upload_panel(api_base: str):
    """Upload + summary + mock plan comparison."""
    st.subheader("📎 Upload a Travel Document")
    st.caption("Upload a PDF or image. Saved locally to `data/uploads/`. Extraction is mocked for now.")

    file = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg", "webp"])
    if not file:
        return

    with st.spinner("Uploading & extracting…"):
        resp = requests.post(f"{api_base}/upload_extract", files={"file": (file.name, file, file.type)})

    if resp.status_code != 200:
        st.error(f"Server error: {resp.status_code}")
        return

    data = resp.json()
    if not data.get("ok"):
        st.error(f"Upload failed: {data.get('error', 'Unknown error')}")
        return

    st.success(f"✅ Uploaded `{data['filename']}`")
    st.code(data["path"])

    trip = data.get("trip", {})
    quotes = [
        {
            "plan": "TravelEasy QTD032212",
            "medical": "$100,000",
            "cancellation": "$5,000",
            "price": "$42.50",
            "link": "data/samples/TravelEasy Policy QTD032212.pdf",
        },
        {
            "plan": "TravelEasy Pre-Ex QTD032212-PX",
            "medical": "$100,000 (Pre-Existing)",
            "cancellation": "$4,000",
            "price": "$49.90",
            "link": "data/samples/TravelEasy Pre-Ex Policy QTD032212-PX.pdf",
        },
        {
            "plan": "Scootsurance QSR022206",
            "medical": "$80,000",
            "cancellation": "$3,000",
            "price": "$38.00",
            "link": "data/samples/Scootsurance QSR022206_updated.pdf",
        },
    ]

    # Pick recommended plan based on simple logic
    recommended = quotes[2] if trip.get("trip_cost", 0) < 3000 else quotes[0]

    st.session_state["last_trip"] = trip
    _render_trip_summary(trip)

    st.divider()
    st.subheader("💸 Insurance Plan Comparison")

    for q in quotes:
        highlight = "🟢 **Recommended**" if q["plan"] == recommended["plan"] else ""
        st.markdown(
            f"""
**{q['plan']}**  
• Medical Coverage: `{q['medical']}`  
• Trip Cancellation: `{q['cancellation']}`  
• Price: `{q['price']}`  
{highlight}  
[📄 View Policy PDF]({q['link']})
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.success(f"✅ Recommended Plan: **{recommended['plan']}** ({recommended['price']})")

    if st.button("🛒 Proceed to Quote ➜", use_container_width=True):
        st.info(f"Next step: Quote generation for **{recommended['plan']}** (mock flow).")