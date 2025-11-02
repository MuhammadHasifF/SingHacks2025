# components/upload_panel.py
# Enhanced version with separate itinerary and ticket uploads

import json
import mimetypes
from pathlib import Path
from datetime import datetime

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


def _calculate_duration_from_dates(dates_str: str) -> int:
    """
    Calculate duration in days from a date range string.
    Format: "YYYY-MM-DD to YYYY-MM-DD"
    
    Returns number of days or 0 if parsing fails.
    """
    if not dates_str or dates_str == "None":
        return 0
    
    try:
        # Try to parse "YYYY-MM-DD to YYYY-MM-DD"
        if " to " in dates_str:
            parts = dates_str.split(" to ")
            if len(parts) == 2:
                start_date = datetime.strptime(parts[0].strip(), "%Y-%m-%d")
                end_date = datetime.strptime(parts[1].strip(), "%Y-%m-%d")
                delta = end_date - start_date
                return max(1, delta.days)  # At least 1 day
    except:
        pass
    
    return 0


def _render_trip_summary(trip: dict):
    """Display comprehensive trip summary with all extracted information."""
    with st.container(border=True):
        st.markdown("### Trip Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            travelers = trip.get('traveler_names') or trip.get('traveler_name') or trip.get('passenger_details')
            st.markdown(f"**Traveler(s):** {travelers if travelers else 'None'}")
            st.markdown(f"**Destination:** {trip.get('destination', 'None')}")
            st.markdown(f"**Dates:** {trip.get('dates', 'None')}")
            duration = trip.get('duration')
            st.markdown(f"**Duration:** {f'{duration} days' if duration else 'None'}")
        
        with col2:
            st.markdown(f"**Trip Cost:** {_fmt_cost(trip.get('trip_cost', 0))}")
            st.markdown(f"**Flight:** {trip.get('flight_info', 'None')}")
            st.markdown(f"**Passengers:** {trip.get('passenger_details', 'None')}")
            if trip.get('special_requirements'):
                st.markdown(f"**Special Requirements:** {trip.get('special_requirements', 'None')}")
        
        # Additional details
        if trip.get('location') or trip.get('activities') or trip.get('timeline') or trip.get('trip_purpose'):
            st.divider()
            with st.expander("Additional Trip Details", expanded=False):
                if trip.get('location'):
                    st.markdown(f"**Locations:** {trip.get('location')}")
                if trip.get('activities'):
                    st.markdown(f"**Activities:** {trip.get('activities')}")
                if trip.get('timeline'):
                    st.markdown(f"**Timeline:** {trip.get('timeline')}")
                if trip.get('trip_purpose'):
                    st.markdown(f"**Trip Purpose:** {trip.get('trip_purpose')}")


def _render_quotes(quotes: list[dict], recommended_plan: str):
    st.divider()
    st.subheader("Insurance Plan Comparison")
    for q in quotes:
        highlight = "**Recommended**" if q["plan"] == recommended_plan else ""
        
        # Build coverage details with all available fields
        coverage_lines = []
        if q.get('medical') and q.get('medical') != "$0":
            coverage_lines.append(f"• Medical: `{q['medical']}`")
        if q.get('cancellation') and q.get('cancellation') != "$0":
            coverage_lines.append(f"• Trip Cancellation: `{q['cancellation']}`")
        if q.get('death_disablement') and q.get('death_disablement') != "$0":
            coverage_lines.append(f"• Accidental Death/Disablement: `{q['death_disablement']}`")
        if q.get('dental') and q.get('dental') != "$0":
            coverage_lines.append(f"• Emergency Dental: `{q['dental']}`")
        if q.get('travel_delay') and q.get('travel_delay') != "$0":
            coverage_lines.append(f"• Travel Delay: `{q['travel_delay']}`")
        
        coverage_text = "\n".join(coverage_lines) if coverage_lines else "• Coverage details in policy PDF"
        
        st.markdown(
            f"""
**{q['plan']}**  
{coverage_text}
• Price: `{q['price']}`  
{highlight}  
[View Policy PDF]({q['link']})
            """,
            unsafe_allow_html=True,
        )
    st.divider()
    price = next((q["price"] for q in quotes if q["plan"] == recommended_plan), "—")
    st.success(f"Recommended Plan: {recommended_plan} ({price})")


def _merge_trip_data(itinerary_data: dict, ticket_data: dict) -> dict:
    """Merge itinerary and ticket data into complete trip information."""
    merged = {}
    
    # Start with itinerary data (destination, dates, costs)
    merged.update(itinerary_data)
    
    # Calculate duration from both itinerary and ticket dates
    itinerary_duration = _calculate_duration_from_dates(itinerary_data.get("dates", ""))
    ticket_duration = _calculate_duration_from_dates(ticket_data.get("dates", ""))
    
    # Use the longer duration if ticket has dates
    if ticket_duration > 0:
        # Also check explicit duration field
        ticket_explicit_duration = ticket_data.get("duration", 0) or 0
        ticket_duration = max(ticket_duration, ticket_explicit_duration)
        
        # Take the maximum duration from either source
        itinerary_explicit_duration = itinerary_data.get("duration", 0) or 0
        itinerary_duration = max(itinerary_duration, itinerary_explicit_duration)
        
        final_duration = max(itinerary_duration, ticket_duration)
        
        # If ticket has dates and no itinerary dates, use ticket dates
        if ticket_duration > 0 and itinerary_duration == 0:
            merged["dates"] = ticket_data.get("dates")
        
        # Set the duration
        merged["duration"] = final_duration
    
    # Override/add ticket-specific information
    # Use traveler_names from ticket if available
    if ticket_data.get("traveler_names"):
        merged["traveler_names"] = ticket_data.get("traveler_names")
    elif ticket_data.get("passenger_details"):
        merged["traveler_names"] = ticket_data.get("passenger_details")
    
    # Add passenger info from ticket
    merged["passenger_count"] = ticket_data.get("passenger_count", 1)
    merged["passenger_details"] = ticket_data.get("passenger_details")
    merged["special_requirements"] = ticket_data.get("special_requirements")
    
    # Keep all itinerary fields
    if itinerary_data.get("traveler_name"):
        if not merged.get("traveler_names"):
            merged["traveler_names"] = itinerary_data.get("traveler_name")
    
    return merged


def render_upload_panel(api_base: str):
    """Enhanced upload panel with separate itinerary and ticket uploads."""
    st.header("Quick Buy Insurance")
    st.caption("Upload your travel documents for instant quotes and personalized recommendations.")
    
    # Initialize session
    sid = st.session_state.get("session_id") or "default"
    
    # Load saved data
    saved = _load_payload(sid)
    
    # Two upload sections: Itinerary and Ticket
    with st.container(border=True):
        st.markdown("#### Step 1: Upload Itinerary")
        st.caption("Upload your travel itinerary (destination, dates, flight details)")
        
        col1, col2 = st.columns(2)
        
        itinerary_file = col1.file_uploader(
            "Choose itinerary file", 
            type=["pdf", "png", "jpg", "jpeg", "webp"],
            key="itinerary_uploader"
        )
        
        # Show saved itinerary status
        if saved.get("itinerary_data"):
            col2.success("Itinerary uploaded")
            col2.write(f"**Destination:** {saved.get('itinerary_data', {}).get('destination', '—')}")
            col2.write(f"**Dates:** {saved.get('itinerary_data', {}).get('dates', '—')}")
        else:
            col2.info("No itinerary uploaded yet")
        
        # Upload itinerary - check if this is a new file
        if itinerary_file:
            last_processed = st.session_state.get("last_itinerary_file", None)
            if itinerary_file.name != last_processed:
                with st.spinner("Extracting itinerary information..."):
                    files = {"file": (itinerary_file.name, itinerary_file, itinerary_file.type)}
                    data = {"doc_type": "itinerary"}
                    
                    resp = requests.post(
                        f"{api_base}/upload_extract",
                        files=files,
                        data=data,
                        timeout=120,
                    )
                    
                    if resp.status_code == 200:
                        result = resp.json()
                        if result.get("ok"):
                            saved["itinerary_data"] = result.get("data", {})
                            st.session_state["last_itinerary_file"] = itinerary_file.name
                            st.success(f"Extracted itinerary from {itinerary_file.name}")
                            _save_payload(sid, saved)
                            st.rerun()
                        else:
                            st.error(f"Extraction failed: {result.get('error', 'Unknown error')}")
                    else:
                        st.error(f"Upload failed: {resp.status_code}")
    
    with st.container(border=True):
        st.markdown("#### Step 2: Upload Ticket Information")
        st.caption("Upload your booking/ticket (passengers, personal info)")
        
        col1, col2 = st.columns(2)
        
        ticket_file = col1.file_uploader(
            "Choose ticket file", 
            type=["pdf", "png", "jpg", "jpeg", "webp"],
            key="ticket_uploader"
        )
        
        # Show saved ticket status
        if saved.get("ticket_data"):
            col2.success("Ticket information uploaded")
            ticket_info = saved.get('ticket_data', {})
            col2.write(f"**Passengers:** {ticket_info.get('passenger_details', '—')}")
            if ticket_info.get('dates'):
                col2.write(f"**Dates:** {ticket_info.get('dates', '—')}")
        else:
            col2.info("No ticket uploaded yet")
        
        # Upload ticket - check if this is a new file
        if ticket_file:
            last_processed = st.session_state.get("last_ticket_file", None)
            if ticket_file.name != last_processed:
                with st.spinner("Extracting ticket information..."):
                    files = {"file": (ticket_file.name, ticket_file, ticket_file.type)}
                    data = {"doc_type": "ticket"}
                    
                    resp = requests.post(
                        f"{api_base}/upload_extract",
                        files=files,
                        data=data,
                        timeout=120,
                    )
                    
                    if resp.status_code == 200:
                        result = resp.json()
                        if result.get("ok"):
                            saved["ticket_data"] = result.get("data", {})
                            st.session_state["last_ticket_file"] = ticket_file.name
                            st.success(f"Extracted ticket info from {ticket_file.name}")
                            _save_payload(sid, saved)
                            st.rerun()
                        else:
                            st.error(f"Extraction failed: {result.get('error', 'Unknown error')}")
                    else:
                        st.error(f"Upload failed: {resp.status_code}")
    
    # Generate Quotes section
    if saved.get("itinerary_data") or saved.get("ticket_data"):
        st.divider()
        
        if st.button("Generate Insurance Quotes", use_container_width=True, type="primary"):
            with st.spinner("Analyzing your trip and generating recommendations..."):
                # Merge data
                merged_trip = _merge_trip_data(
                    saved.get("itinerary_data", {}),
                    saved.get("ticket_data", {})
                )
                
                # Generate quotes via API
                resp = requests.post(
                    f"{api_base}/generate_quotes",
                    json={"trip_data": merged_trip},
                    timeout=120,
                )
                
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get("ok"):
                        saved["trip"] = result.get("trip", merged_trip)
                        saved["quotes"] = result.get("quotes", [])
                        saved["recommended_plan"] = result.get("recommended_plan", "")
                        _save_payload(sid, saved)
                        st.success("Insurance recommendations ready!")
                        st.rerun()
                    else:
                        st.error(f"Quote generation failed: {result.get('error', 'Unknown error')}")
                else:
                    st.error(f"API error: {resp.status_code}")
    
    # Display saved information and quotes
    if saved.get("trip") and saved.get("quotes"):
        st.divider()
        _render_trip_summary(saved["trip"])
        _render_quotes(saved.get("quotes", []), saved.get("recommended_plan", ""))
        
        # Payment functionality
        quotes = saved.get("quotes", [])
        recommended = saved.get("recommended_plan", "")
        
        # Show payment success message if payment was confirmed
        if st.session_state.get("payment_confirmed"):
            st.success("🎉 Payment confirmed successfully! Your insurance policy is now active.")
            st.balloons()
            st.session_state.payment_confirmed = False
        
        # Proceed to Payment button
        if st.button("Proceed to Payment ➜", use_container_width=True, type="primary", key="proceed_payment"):
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
                                checkout_url = checkout_result.get("url") or checkout_result.get("checkout_url")
                                
                                if checkout_url:
                                    # Store payment info in session state for payment page
                                    st.session_state["current_payment_intent"] = payment_intent_id
                                    st.session_state["checkout_url"] = checkout_url
                                    st.session_state["payment_product_name"] = recommended
                                    st.session_state["payment_amount"] = amount_cents
                                    st.session_state["payment_status"] = "ready"
                                    
                                    # Navigate to payment page using query params
                                    st.query_params = {
                                        **st.query_params,
                                        "page": "payment",
                                        "payment_intent": payment_intent_id
                                    }
                                    st.rerun()
                                else:
                                    st.warning("⚠️ Checkout URL not found in response.")
                                    st.json(checkout_result)  # Show response for debugging
                            else:
                                error_detail = "Unknown error"
                                try:
                                    error_data = checkout_response.json()
                                    error_detail = error_data.get("detail", error_data.get("error", checkout_response.text))
                                except:
                                    error_detail = checkout_response.text
                                
                                st.error(f"❌ Stripe checkout creation failed: {checkout_response.status_code}")
                                st.error(f"Error details: {error_detail}")
                        except Exception as checkout_error:
                            st.error(f"❌ Error creating Stripe checkout: {checkout_error}")
                            import traceback
                            st.code(traceback.format_exc())
                    else:
                        error_detail = "Unknown error"
                        try:
                            error_data = response.json()
                            error_detail = error_data.get("detail", error_data.get("error", response.text))
                        except:
                            error_detail = response.text
                        
                        st.error(f"❌ Payment intent creation failed: {response.status_code}")
                        st.error(f"Error details: {error_detail}")
                except Exception as e:
                    st.error(f"❌ Error calling payment API: {e}")

