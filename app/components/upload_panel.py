# components/upload_panel.py

import json
import mimetypes
from pathlib import Path

import requests
import streamlit as st

SESS_DIR = Path(".sessions")
SESS_DIR.mkdir(exist_ok=True)


def _store_path(sid: str) -> Path:
    return SESS_DIR / f"{sid}.trip.json"


def _save_payload(sid: str, payload: dict) -> None:
    _store_path(sid).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _load_payload(sid: str) -> dict:
    p = _store_path(sid)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _fmt_cost(val):
    try:
        return f"${float(val):,.2f}"
    except Exception:
        return str(val) if val is not None else "—"


def _render_trip_summary(trip: dict):
    with st.container(border=True):
        st.markdown("### Trip Summary (Preview)")
        st.markdown(f"**Traveler:** {trip.get('traveler_name', '—')}")
        st.markdown(f"**Destination:** {trip.get('destination', '—')}")
        st.markdown(f"**Dates:** {trip.get('dates', '—')}")
        st.markdown(f"**Trip Cost:** {_fmt_cost(trip.get('trip_cost', '—'))}")


def _render_quotes(quotes: list[dict], recommended_plan: str):
    st.divider()
    st.subheader("Insurance Plan Comparison")
    for q in quotes:
        highlight = "**Recommended**" if q["plan"] == recommended_plan else ""
        st.markdown(
            f"""
**{q['plan']}**  
• Medical Coverage: `{q['medical']}`  
• Trip Cancellation: `{q['cancellation']}`  
• Price: `{q['price']}`  
{highlight}  
[View Policy PDF]({q['link']})
            """,
            unsafe_allow_html=True,
        )
    st.divider()
    price = next((q["price"] for q in quotes if q["plan"] == recommended_plan), "—")
    # Keep Streamlit's green success highlight for the recommended plan
    st.success(f"Recommended Plan: {recommended_plan} ({price})")


def _guess_mime(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def render_upload_panel(api_base: str):
    """Upload + summary + mock plan comparison with stored-file UX and immediate UI updates."""
    st.subheader("Upload a Travel Document")
    st.caption("Upload a PDF or image. Saved locally to data/uploads/. Extraction is mocked for now.")

    # From main.py (must be initialized before calling this)
    sid = st.session_state.get("session_id") or dict(st.query_params).get("sid") or "default"

    # Panel mode: 'stored' (show current file info) or 'upload' (show uploader)
    if "upload_panel_mode" not in st.session_state:
        saved = _load_payload(sid)
        saved_path = Path(saved.get("path", "")) if saved else None
        st.session_state.upload_panel_mode = "stored" if (saved and saved_path and saved_path.exists()) else "upload"

    mode = st.session_state.upload_panel_mode
    saved = _load_payload(sid)
    saved_path = Path(saved.get("path", "")) if saved else None
    saved_filename = saved.get("filename") if saved else None

    # -------- Stored file view --------
    if mode == "stored" and saved and saved_path and saved_path.exists():
        with st.container(border=True):
            st.markdown("#### Current File (stored)")
            st.markdown(f"**File:** `{saved_filename or saved_path.name}`")
            st.caption(f"Location on server: `{saved_path}`")

            col1, col2, col3, col4 = st.columns(4)

            # Reuse: rerun extraction without asking user to upload again
            with col1:
                if st.button("Reuse this file", use_container_width=True, type="primary"):
                    try:
                        with open(saved_path, "rb") as f:
                            resp = requests.post(
                                f"{api_base}/upload_extract",
                                files={"file": (saved_filename or saved_path.name, f, _guess_mime(saved_filename or saved_path.name))},
                                timeout=120,
                            )
                        if resp.status_code != 200:
                            st.error(f"Server error: {resp.status_code}")
                        else:
                            data = resp.json()
                            if not data.get("ok"):
                                st.error(f"Upload failed: {data.get('error', 'Unknown error')}")
                            else:
                                trip2 = data.get("trip", {})
                                # local quotes list (mock)
                                quotes = [
                                    {"plan": "TravelEasy QTD032212", "medical": "$100,000", "cancellation": "$5,000",
                                     "price": "$42.50", "link": "data/samples/TravelEasy Policy QTD032212.pdf"},
                                    {"plan": "TravelEasy Pre-Ex QTD032212-PX", "medical": "$100,000 (Pre-Existing)",
                                     "cancellation": "$4,000", "price": "$49.90",
                                     "link": "data/samples/TravelEasy Pre-Ex Policy QTD032212-PX.pdf"},
                                    {"plan": "Scootsurance QSR022206", "medical": "$80,000",
                                     "cancellation": "$3,000", "price": "$38.00",
                                     "link": "data/samples/Scootsurance QSR022206_updated.pdf"},
                                ]
                                try:
                                    tc = float(trip2.get("trip_cost", 0) or 0)
                                except Exception:
                                    tc = 0.0
                                recommended = "Scootsurance QSR022206" if tc < 3000 else "TravelEasy QTD032212"

                                _save_payload(
                                    sid,
                                    {
                                        "trip": trip2,
                                        "quotes": quotes,
                                        "recommended_plan": recommended,
                                        "filename": saved_filename or saved_path.name,
                                        "path": str(saved_path),
                                    },
                                )
                                # refresh UI immediately
                                st.session_state.upload_panel_mode = "stored"
                                st.rerun()
                    except Exception as e:
                        st.error(f"Reuse failed: {e}")

            # Download
            with col2:
                try:
                    with open(saved_path, "rb") as f:
                        st.download_button("Download", f, file_name=saved_filename or saved_path.name, use_container_width=True)
                except Exception:
                    st.caption("Download unavailable from this process.")

            # Replace -> switch to uploader mode
            with col3:
                if st.button("Replace file", use_container_width=True, type="primary"):
                    st.session_state.upload_panel_mode = "upload"
                    st.rerun()

            # Remove -> delete server file + clear record, switch to upload mode
            with col4:
                if st.button("Remove file", type="secondary", use_container_width=True):
                    try:
                        r = requests.post(f"{api_base}/delete_upload", json={"path": str(saved_path)}, timeout=60)
                        ok = (r.status_code == 200 and r.json().get("ok"))
                        if not ok:
                            st.error(f"Delete failed: {r.text}")
                        else:
                            _save_payload(sid, {})  # clear local record
                            st.session_state.upload_panel_mode = "upload"
                            st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")

        # Render summary below the controls
        trip = saved.get("trip", {})
        quotes = saved.get("quotes", [])
        recommended = saved.get("recommended_plan")
        _render_trip_summary(trip)
        if quotes and recommended:
            _render_quotes(quotes, recommended)
        
        # Show payment success message if payment was confirmed from main.py
        if st.session_state.get("payment_confirmed"):
            st.success("🎉 Payment confirmed successfully! Your insurance policy is now active.")
            st.balloons()
            # Clear the flag
            st.session_state.payment_confirmed = False

        # >>> Restored: Proceed to Quote button <<<
        if st.button("Proceed to Quote ➜", use_container_width=True, type="primary"):
            # Get the price for the recommended plan
            recommended_quote = next((q for q in quotes if q["plan"] == recommended), None)
            if recommended_quote:
                price_str = recommended_quote.get("price", "—")
                
                # Parse price from "$42.50" to cents (4250)
                import re
                price_clean = re.sub(r'[^\d.]', '', str(price_str))
                try:
                    amount_cents = int(float(price_clean) * 100)
                except (ValueError, TypeError):
                    st.error(f"Invalid price format: {price_str}")
                    return
                
                # Get session ID
                session_id = st.session_state.get("session_id", "default")
                
                # Call /payment-intent API
                try:
                    response = requests.post(
                        f"{api_base}/payment-intent",
                        json={
                            "session_user_id": session_id,
                            "product_name": recommended,
                            "purchase_amount": amount_cents
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        payment_intent_id = result.get("payment_intent_id")
                        st.success(f"✅ Payment intent created: {payment_intent_id}")
                        
                        # Call /payment-status/{payment_intent_id} API
                        try:
                            status_response = requests.get(
                                f"{api_base}/payment-status/{payment_intent_id}",
                                timeout=10
                            )
                            
                            if status_response.status_code == 200:
                                payment_status = status_response.text
                                if payment_status:
                                    st.info(f"📊 Payment Status: {payment_status}")
                                else:
                                    st.warning("⚠️ Payment status not found")
                            else:
                                st.warning(f"⚠️ Could not check payment status: {status_response.status_code}")
                        except Exception as status_error:
                            st.warning(f"⚠️ Error checking payment status: {status_error}")
                        
                        # Call /stripe-checkout POST API
                        try:
                            checkout_response = requests.post(
                                f"{api_base}/stripe-checkout",
                                json={
                                    "payment_intent_id": payment_intent_id,
                                    "product_name": recommended,
                                    "purchase_amount": amount_cents
                                },
                                timeout=30
                            )
                            
                            if checkout_response.status_code == 200:
                                checkout_result = checkout_response.json()
                                # Extract URL from Stripe checkout session response
                                checkout_url = checkout_result.get("url") or checkout_result.get("checkout_url")
                                checkout_session_id = checkout_result.get("id") or checkout_result.get("session_id")
                                
                                if checkout_url:
                                    # Store session IDs for later confirmation
                                    st.session_state["current_payment_intent"] = payment_intent_id
                                    if checkout_session_id:
                                        st.session_state["checkout_session_id"] = checkout_session_id
                                    
                                    st.success("✅ Stripe checkout session created!")
                                    # Redirect user to checkout URL
                                    st.markdown(
                                        f'<meta http-equiv="refresh" content="0;url={checkout_url}">',
                                        unsafe_allow_html=True
                                    )
                                    st.link_button("🔗 Complete Payment →", checkout_url, use_container_width=True, type="primary")
                                else:
                                    # If URL is not directly available, try to construct from session ID
                                    st.warning("⚠️ Checkout URL not found in response. Response: " + str(checkout_result)[:200])
                            else:
                                st.error(f"❌ Stripe checkout creation failed: {checkout_response.status_code}")
                        except Exception as checkout_error:
                            st.error(f"❌ Error creating Stripe checkout: {checkout_error}")
                    else:
                        st.error(f"❌ Payment intent creation failed: {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error calling payment API: {e}")
            
        return

    # -------- Uploader view --------
    file = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg", "webp"])
    if not file:
        # If no new file and we still have saved data, show it in a collapsible section
        if saved:
            with st.expander("Previously stored details", expanded=False):
                trip = saved.get("trip", {})
                quotes = saved.get("quotes", [])
                recommended = saved.get("recommended_plan")
                _render_trip_summary(trip)
                if quotes and recommended:
                    _render_quotes(quotes, recommended)

                # >>> Restored: Proceed to Quote button (when viewing saved details in expander) <<<
                if quotes and recommended and st.button("Proceed to Quote ➜", use_container_width=True, type="primary", key="proceed_expander"):
                    st.info(f"Next step: Quote generation for {recommended} (mock flow).")
        return

    with st.spinner("Uploading and extracting..."):
        resp = requests.post(
            f"{api_base}/upload_extract",
            files={"file": (file.name, file, file.type)},
            timeout=120,
        )

    if resp.status_code != 200:
        st.error(f"Server error: {resp.status_code}")
        return

    data = resp.json()
    if not data.get("ok"):
        st.error(f"Upload failed: {data.get('error', 'Unknown error')}")
        return

    st.success(f"Uploaded {data['filename']}")
    st.code(data["path"])

    trip = data.get("trip", {})
    quotes = [
        {"plan": "TravelEasy QTD032212", "medical": "$100,000", "cancellation": "$5,000",
         "price": "$42.50", "link": "data/samples/TravelEasy Policy QTD032212.pdf"},
        {"plan": "TravelEasy Pre-Ex QTD032212-PX", "medical": "$100,000 (Pre-Existing)",
         "cancellation": "$4,000", "price": "$49.90",
         "link": "data/samples/TravelEasy Pre-Ex Policy QTD032212-PX.pdf"},
        {"plan": "Scootsurance QSR022206", "medical": "$80,000", "cancellation": "$3,000",
         "price": "$38.00", "link": "data/samples/Scootsurance QSR022206_updated.pdf"},
    ]
    try:
        tc = float(trip.get("trip_cost", 0) or 0)
    except Exception:
        tc = 0.0
    recommended = "Scootsurance QSR022206" if tc < 3000 else "TravelEasy QTD032212"

    _save_payload(
        sid,
        {
            "trip": trip,
            "quotes": quotes,
            "recommended_plan": recommended,
            "filename": data.get("filename"),
            "path": data.get("path"),
        },
    )

    # Show results for this upload
    _render_trip_summary(trip)
    _render_quotes(quotes, recommended)

    # >>> Restored: Proceed to Quote button for fresh uploads <<<
    if st.button("Proceed to Quote ➜", use_container_width=True, type="primary", key="proceed_after_upload"):
        st.info(f"Next step: Quote generation for {recommended} (mock flow).")

    # Switch to stored mode and rerun so future refreshes show the stored file panel
    st.session_state.upload_panel_mode = "stored"
    st.rerun()
