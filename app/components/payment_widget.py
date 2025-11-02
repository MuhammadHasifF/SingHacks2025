"""
Payment Widget Component
Renders the payment page when user clicks "Proceed to Payment"
"""
import streamlit as st
import requests


def render_payment_page(api_base: str):
    """Render the payment checkout page."""
    
    # Get payment info from session state or query params
    payment_intent_id = st.session_state.get("current_payment_intent") or st.query_params.get("payment_intent")
    checkout_url = st.session_state.get("checkout_url")
    product_name = st.session_state.get("payment_product_name", "Travel Insurance Policy")
    amount_cents = st.session_state.get("payment_amount", 0)
    
    # If amount is 0 or missing, or product name is default, try to get from saved trip data
    if amount_cents == 0 or amount_cents is None or product_name == "Travel Insurance Policy":
        sid = st.session_state.get("session_id", "default")
        try:
            from pathlib import Path
            import json
            sess_dir = Path(".sessions")
            trip_file = sess_dir / f"{sid}.trip.json"
            if trip_file.exists():
                trip_data = json.loads(trip_file.read_text(encoding="utf-8"))
                quotes = trip_data.get("quotes", [])
                recommended = trip_data.get("recommended_plan", "")
                
                # Update product name if we have a recommended plan
                if recommended and product_name == "Travel Insurance Policy":
                    product_name = recommended
                    st.session_state["payment_product_name"] = product_name
                
                # Update amount if missing
                if quotes and recommended and (amount_cents == 0 or amount_cents is None):
                    recommended_quote = next((q for q in quotes if q["plan"] == recommended), None)
                    if recommended_quote:
                        price_str = recommended_quote.get("price", "—")
                        import re
                        price_clean = re.sub(r'[^\d.]', '', str(price_str))
                        try:
                            amount_cents = int(float(price_clean) * 100)
                            # Update session state for next time
                            st.session_state["payment_amount"] = amount_cents
                        except (ValueError, TypeError):
                            pass
        except Exception:
            pass
    
    # Calculate amount in dollars for display
    amount_dollars = (amount_cents / 100.0) if amount_cents and amount_cents > 0 else 0.0
    
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
            <div style="width:10px;height:28px;background:#E4002B;border-radius:6px;"></div>
            <h1 style="margin:0;">Complete Your Payment</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.divider()
    
    # Payment summary
    with st.container(border=True):
        st.markdown("### Payment Summary")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Product:** {product_name}")
            if payment_intent_id:
                st.markdown(f"**Payment Intent ID:** `{payment_intent_id}`")
            else:
                st.markdown("**Payment Intent ID:** `None`")
        
        with col2:
            if amount_dollars > 0:
                st.markdown(f"**Amount:** ${amount_dollars:,.2f} SGD")
            else:
                st.warning("**Amount:** Not available - please return to quotes and try again")
    
    st.divider()
    
    # Checkout button
    if checkout_url:
        st.markdown("### Secure Checkout")
        st.info("You will be redirected to Stripe's secure payment page to complete your purchase.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Use only Streamlit link button (removed duplicate HTML button)
            st.link_button(
                "🔒 Complete Payment Securely →",
                checkout_url,
                use_container_width=True,
                type="primary"
            )
    
    # Back button
    st.divider()
    if st.button("← Back to Quotes", use_container_width=True):
        # Remove payment page from query params
        params = dict(st.query_params)
        params.pop("page", None)
        params.pop("payment_intent", None)
        st.query_params = params
        st.rerun()
    
    # Payment status check (optional - can poll for status)
    if payment_intent_id:
        with st.expander("Check Payment Status", expanded=False):
            if st.button("Refresh Status"):
                try:
                    status_resp = requests.get(
                        f"{api_base}/payment-status/{payment_intent_id}",
                        timeout=10
                    )
                    if status_resp.status_code == 200:
                        status_data = status_resp.json()
                        payment_status = status_data.get("payment_status", "unknown")
                        
                        if payment_status == "completed":
                            st.success("✅ Payment completed successfully!")
                            st.balloons()
                            st.session_state["payment_confirmed"] = True
                        elif payment_status == "pending":
                            st.info("⏳ Payment is pending. Please complete the checkout process.")
                        elif payment_status == "failed":
                            st.error("❌ Payment failed. Please try again.")
                        else:
                            st.warning(f"⚠️ Payment status: {payment_status}")
                    else:
                        st.warning("Could not check payment status.")
                except Exception as e:
                    st.error(f"Error checking status: {e}")
