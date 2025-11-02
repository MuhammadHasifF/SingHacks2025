"""
Payment Widget Component
Renders the payment page when user clicks "Proceed to Payment"
"""
import streamlit as st
import requests


def render_payment_page(api_base: str):
    """Render the payment checkout page."""
    
    # Get payment info from session state
    payment_intent_id = st.session_state.get("current_payment_intent")
    checkout_url = st.session_state.get("checkout_url")
    product_name = st.session_state.get("payment_product_name", "Travel Insurance Policy")
    amount_cents = st.session_state.get("payment_amount", 0)
    
    # Calculate amount in dollars for display
    amount_dollars = amount_cents / 100.0
    
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
            st.markdown(f"**Payment Intent ID:** `{payment_intent_id}`")
        
        with col2:
            st.markdown(f"**Amount:** ${amount_dollars:,.2f} SGD")
    
    st.divider()
    
    # Checkout button
    if checkout_url:
        st.markdown("### Secure Checkout")
        st.info("You will be redirected to Stripe's secure payment page to complete your purchase.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                f'<a href="{checkout_url}" target="_self">'
                '<button style="background-color: #E4002B; color: white; padding: 15px 40px; '
                'border: none; border-radius: 12px; cursor: pointer; width: 100%; '
                'font-size: 18px; font-weight: bold; box-shadow: 0 6px 14px rgba(228,0,43,.3);">'
                '🔒 Complete Payment Securely →'
                '</button></a>',
                unsafe_allow_html=True
            )
            
            # Alternative: Use Streamlit link button
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
