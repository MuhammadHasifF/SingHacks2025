"""
backend/api.py
--------------
FastAPI bridge for the frontend. Exposes:
  - GET  /health
  - POST /chat
  - POST /upload
  - POST /upload_extract
  - POST /payment-intent
  - POST /stripe-checkout
  - GET  /payment-status/{payment_intent_id}
  - POST /webhook/stripe
"""

import os
import json
import traceback
import time
import uuid
import logging
from urllib.parse import quote as urlquote
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

import stripe
import boto3
import requests

# 🧠 Internal modules
from backend.chains.conversational_agent import create_insurance_agent
from backend.chains.response_formatter import format_response
from backend.chains.intent import detect_intent
from backend.chains.policy_comparator import load_all_policies
from backend.ingestion.pdf_loader import extract_text_from_pdf
from backend.utils.policy_extractor import (
    init_llm, 
    extract_itinerary_info,
    extract_ticket_info,
    extract_policy_summary, 
    get_recommended_plan,
    calculate_dynamic_price
)
from backend.utils.taxonomy_reader import load_policy_coverage


# ---------------------------------------------------------------------------- #
# ⚙️ FastAPI Initialization
# ---------------------------------------------------------------------------- #
app = FastAPI(title="Insurance Scammer API", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEBUG = os.getenv("DEBUG", "0") == "1"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@app.get("/health")
def health():
    return {
        "ok": True,
        "groq_key_set": bool(GROQ_API_KEY),
        "stripe_configured": bool(STRIPE_SECRET_KEY),
        "stripe_api_key_set": bool(stripe.api_key if STRIPE_SECRET_KEY else False),
        "dynamodb_configured": payments_table is not None,
    }

@app.get("/policy_pdf/{filename}")
async def get_policy_pdf(filename: str):
    """Serve policy PDF files."""
    pdf_path = os.path.join("data/Policy_Wordings", filename)
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf")
    return {"error": "PDF not found"}

# ---------------------------------------------------------------------------- #
# 🤖 Chatbot Endpoint (/chat)
# ---------------------------------------------------------------------------- #
agent = create_insurance_agent()  # singleton in-memory

def _classify_error_message(err: str) -> str:
    low = err.lower()
    if "invalid api key" in low or "invalid_api_key" in low or "401" in low:
        return "Authentication failed: invalid API key. Check GROQ_API_KEY on the server."
    if "request too large" in low or "tpm" in low or "413" in low or "tokens per minute" in low:
        return "Request exceeded the model's token/context limit. Reduce PDF chunk size or shorten input."
    if "connection" in low or "timeout" in low or "dns" in low or "failed to establish" in low:
        return "Cannot reach the LLM server. Check network or Groq availability."
    return "Sorry, I ran into an error processing that. Please try again."

@app.post("/chat")
async def chat(request: Request):
    """Handle user chatbot questions."""
    payload = await request.json()
    question = (payload.get("question") or "").strip()
    session_id = payload.get("session_id") or "default"

    if not question:
        return format_response(
            text="Please ask a question (e.g., 'Compare medical coverage').",
            session_id=session_id,
            intent="general",
            citations=[],
        )

    if not GROQ_API_KEY:
        return format_response(
            text="Server misconfiguration: GROQ_API_KEY is missing.",
            session_id=session_id,
            intent="error",
            citations=[],
            meta={"error": "GROQ_API_KEY not set"},
        )

    try:
        # 1️⃣ Detect intent (metadata)
        intent = detect_intent(question)

        # 2️⃣ Generate answer (LLM + JSON logic)
        answer_text = agent(session_id, question)

        # 3️⃣ Return structured response
        return format_response(
            text=answer_text,
            session_id=session_id,
            intent=intent,
            citations=["MSIG TravelEasy / Pre-Ex / Scootsurance Official Policy Wordings (2025)"],
            meta={"model": "llama-3.3-70b-versatile"},
        )

    except Exception as e:
        err = str(e)
        user_msg = _classify_error_message(err)

        # Small traceback tail for dev visibility
        tb_tail = ""
        if DEBUG:
            tb_tail = "".join(traceback.format_exc()[-800:])  # last ~800 chars

        return format_response(
            text=user_msg,
            session_id=session_id,
            intent="error",
            citations=[],
            meta={"error": err, "detail": tb_tail},
        )

# ---------------------------------------------------------------------------- #
# 📎 Upload Endpoints
# ---------------------------------------------------------------------------- #
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return {"ok": True, "filename": file.filename, "path": file_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/upload_extract")
async def upload_and_extract(file: UploadFile = File(...), doc_type: str = Form("itinerary")):
    """
    Upload PDF and extract document data using LLM-based extraction.
    
    doc_type: 'itinerary', 'ticket', or 'policy'
    Returns extracted information based on document type.
    """
    try:
        save_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())

        # Extract text from PDF
        pdf_text = extract_text_from_pdf(save_path)
        llm = init_llm()
        
        # Extract based on document type
        if doc_type == "itinerary":
            extracted_data = extract_itinerary_info(llm, pdf_text)
        elif doc_type == "ticket":
            extracted_data = extract_ticket_info(llm, pdf_text)
        elif doc_type == "policy":
            extracted_data = extract_policy_summary(llm, pdf_text)
        else:
            # Default to itinerary
            extracted_data = extract_itinerary_info(llm, pdf_text)

        return {
            "ok": True,
            "filename": file.filename,
            "path": save_path,
            "doc_type": doc_type,
            "data": extracted_data,
        }

    except Exception as e:
        if DEBUG:
            traceback.print_exc()
        return {"ok": False, "error": str(e)}


@app.post("/generate_quotes")
async def generate_quotes(request: Request):
    """
    Generate insurance quotes and recommendations based on accumulated travel data.
    Merges itinerary, ticket, and any existing policy information.
    """
    try:
        payload = await request.json()
        
        # Get accumulated data (merged from itinerary + ticket)
        trip_data = payload.get("trip_data", {})
        
        # Extract trip cost and duration for recommendations
        trip_cost = float(trip_data.get("trip_cost", 0) or 0)
        duration_days = int(trip_data.get("duration", 0) or 7)  # Default to 7 days
        
        # Load existing policies for comparison
        existing_policies = load_all_policies()
        quotes = []
        
        # Add all MSIG policies to comparison
        pdf_base_path = "data/Policy_Wordings"
        pdf_mapping = {
            "TravelEasy Policy QTD032212": "TravelEasy Policy QTD032212.pdf",
            "TravelEasy Pre-Ex Policy QTD032212-PX": "TravelEasy Pre-Ex Policy QTD032212-PX.pdf",
            "Scootsurance QSR022206_updated": "Scootsurance QSR022206_updated.pdf",
        }
        
        for product_name in existing_policies.keys():
            # Load real coverage data from taxonomy files
            coverage = load_policy_coverage(product_name)
            
            if coverage:
                # For display name mapping
                display_name = product_name
                if product_name == "Scootsurance QSR022206_updated":
                    display_name = "Scootsurance QSR022206"
                
                # Generate PDF link using API endpoint with URL encoding
                pdf_filename = pdf_mapping.get(product_name, "")
                pdf_link = f"http://127.0.0.1:8000/policy_pdf/{urlquote(pdf_filename)}" if pdf_filename else ""
                
                # Calculate dynamic price based on trip duration
                dynamic_price = calculate_dynamic_price(product_name, duration_days)
                formatted_price = f"${dynamic_price:.2f}"
                
                quote = {
                    "plan": display_name,
                    "medical": coverage.get("medical", "$0"),
                    "cancellation": coverage.get("cancellation", "$0"),
                    "death_disablement": coverage.get("death_disablement", "$0"),
                    "dental": coverage.get("dental", "$0"),
                    "travel_delay": coverage.get("travel_delay", "$0"),
                    "price": formatted_price,
                    "link": pdf_link,
                }
            else:
                # Fallback if extraction fails
                continue
            
            quotes.append(quote)
        
        # Recommend best plan based on actual trip data
        recommended = get_recommended_plan(quotes, trip_cost)
        if not recommended:
            recommended = quotes[0].get("plan") if quotes else ""

        return {
            "ok": True,
            "trip": trip_data,
            "quotes": quotes,
            "recommended_plan": recommended,
        }

    except Exception as e:
        if DEBUG:
            traceback.print_exc()
        return {"ok": False, "error": str(e)}
    
# ---------------------------------------------------------------------------- #
# Stripe & Payment Configuration
# ---------------------------------------------------------------------------- #

load_dotenv()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
DYNAMODB_PAYMENTS_TABLE = os.getenv("DYNAMODB_PAYMENTS_TABLE", "lea-payments-local")
DDB_ENDPOINT = os.getenv("DDB_ENDPOINT")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# Initialize DynamoDB (optional - payment will work without it)
payments_table = None
dynamodb = None

try:
    # Only initialize DynamoDB if DDB_ENDPOINT is explicitly set (for local DynamoDB)
    # OR if AWS credentials are available
    if DDB_ENDPOINT:
        # Local DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION, endpoint_url=DDB_ENDPOINT)
        payments_table = dynamodb.Table(DYNAMODB_PAYMENTS_TABLE)
        try:
            payments_table.load()
            print(f"✓ DynamoDB table '{DYNAMODB_PAYMENTS_TABLE}' initialized successfully (Local)")
        except Exception as load_error:
            print(f"⚠ Warning: DynamoDB table '{DYNAMODB_PAYMENTS_TABLE}' does not exist or cannot be accessed: {load_error}")
            print("  Table will be created on first write, or you may need to create it manually.")
    else:
        # Don't initialize DynamoDB if DDB_ENDPOINT is not set
        # This avoids trying to authenticate with AWS when credentials aren't available
        print("ℹ DynamoDB not initialized: DDB_ENDPOINT not set. Payment will work without database storage.")
        print("  Set DDB_ENDPOINT for local DynamoDB (e.g., 'http://localhost:8000') if you want database storage.")
except Exception as e:
    print(f"⚠ DynamoDB initialization failed: {e}")
    print("  Payment will work without database storage. This is fine for testing.")
    payments_table = None
    dynamodb = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stripe-webhook")

# API to create payment intent
@app.post("/payment-intent")
async def create_payment_intent(request: Request):
    payload = await request.json()
    payment_intent_id = f"test_payment_{uuid.uuid4().hex[:12]}"
    user_id = "user_" + str(payload.get("session_user_id", "default"))
    quote_id = f"quote_{uuid.uuid4().hex[:8]}"
    amount = payload.get("purchase_amount")
    product_name = payload.get("product_name")

    # Try to save to DynamoDB if available, but don't fail if it's not configured
    if payments_table:
        payment_record = {
            'payment_intent_id': payment_intent_id,
            'user_id': user_id,
            'quote_id': quote_id,
            'payment_status': 'pending',
            'amount': amount,
            'currency': 'SGD',
            'product_name': product_name,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        try:
            payments_table.put_item(Item=payment_record)
            print(f"✓ Payment record created in DynamoDB with ID: {payment_intent_id}")
        except Exception as e:
            print(f"⚠ Warning: Failed to create payment record in DynamoDB: {e}")
            print("  Continuing without database storage (payment will still work)")
    else:
        print(f"ℹ Payment intent created (no database): {payment_intent_id}")
    
    return {
        'payment_intent_id': payment_intent_id,
        'payment_status': 'pending',
        'user_id': user_id
    }


#API to trigger stripe
@app.post('/stripe-checkout')
async def create_stripe_checkout(request: Request):
    if not STRIPE_SECRET_KEY:
        error_msg = "Stripe not configured. Please set STRIPE_SECRET_KEY in environment variables."
        print(f"ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    
    # Ensure Stripe API key is set (in case it wasn't set during initialization)
    if not stripe.api_key:
        stripe.api_key = STRIPE_SECRET_KEY
    
    print("Creating Stripe Checkout Session")
    payload = await request.json()
    
    # Validate required fields
    purchase_amount = payload.get("purchase_amount")
    product_name = payload.get("product_name", "Travel Insurance Policy")
    payment_intent_id = payload.get("payment_intent_id")
    
    if not purchase_amount:
        raise HTTPException(status_code=400, detail="purchase_amount is required")
    
    if not isinstance(purchase_amount, int):
        try:
            purchase_amount = int(purchase_amount)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"Invalid purchase_amount: {purchase_amount}. Must be an integer (amount in cents).")

    try:
        print(f"Creating checkout for: {product_name}, Amount: {purchase_amount} cents")
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'sgd',
                    'unit_amount': purchase_amount,
                    'product_data': {
                        'name': product_name,
                        'description': 'Travel Insurance Policy',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'http://localhost:8501/?payment_success=true&session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url='http://localhost:8501/?payment_cancelled=true',
            client_reference_id=payment_intent_id,
        )
        
        print(f"✓ Stripe Checkout Session created: {checkout_session.id}")
        print(f"  URL: {checkout_session.url}")
        
        # Update DynamoDB if available
        if payments_table and payment_intent_id:
            try:
                payments_table.update_item(
                    Key={'payment_intent_id': payment_intent_id},
                    UpdateExpression='SET stripe_session_id = :sid',
                    ExpressionAttributeValues={':sid': checkout_session.id}
                )
                print(f"✓ Updated DynamoDB with session ID")
            except Exception as db_error:
                print(f"Warning: Could not update DynamoDB with Stripe session ID: {db_error}")
        
        return {
            "id": checkout_session.id,
            "url": checkout_session.url,
            "session_id": checkout_session.id,
            "checkout_url": checkout_session.url
        }
        
    except stripe.error.StripeError as e:
        error_msg = f"Stripe API error: {str(e)}"
        print(f"ERROR: {error_msg}")
        print(f"  Error type: {type(e).__name__}")
        if hasattr(e, 'user_message'):
            print(f"  User message: {e.user_message}")
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to create Stripe checkout session: {str(e)}"
        print(f"ERROR: {error_msg}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@app.get('/payment-status/{payment_intent_id}')
async def check_payment_status(payment_intent_id: str):
    if not payments_table:
        return JSONResponse(content={'payment_status': 'database_not_configured'}, status_code=503)
    
    try:
        response = payments_table.get_item(Key={'payment_intent_id': payment_intent_id})
        item = response.get('Item')
        if item:
            status = item.get('payment_status', 'unknown')
            return JSONResponse(content={'payment_status': status})
        return JSONResponse(content={'payment_status': 'not_found'}, status_code=404)
    except Exception as e:
        print(f"Failed to check payment status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check payment status: {str(e)}")

class DeleteReq(BaseModel):
    path: str

@app.post("/delete_upload")
async def delete_upload(req: DeleteReq):
    try:
        if not req.path:
            return {"ok": False, "error": "no path"}
        if os.path.exists(req.path):
            os.remove(req.path)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Helper function to check Stripe payment status (synchronous)
def check_stripe_payment_status_sync(session_id):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session.payment_status, session
    except Exception as e:
        print(f"Failed to check Stripe status: {e}")
        return None, None

@app.post('/trigger-webhook')
async def trigger_local_webhook(request: Request):
    payload = await request.json()
    print("Triggering local webhook endpoint...")
    
    webhook_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": payload.get("id"),
                "client_reference_id": payload.get('client_reference_id'),
                "payment_intent": payload.get('payment_intent'),
                "payment_status": payload.get('payment_status')
            }
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8086/webhook/stripe",
            json=webhook_event,
            timeout=5
        )
        if response.status_code == 200:
            print("Webhook triggered successfully")
            return True
        else:
            print(f"Webhook returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"Failed to trigger webhook: {e}")
        return False

def wait_for_payment_confirmation(payment_intent_id, session_id):
    """Helper function to poll payment status (synchronous)."""
    print("Checking payment status on Stripe")
    print("Polling Stripe API for payment completion...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        payment_status, session_data = check_stripe_payment_status_sync(session_id)
        
        if payment_status == 'paid':
            print("Payment confirmed on Stripe!")
            print(f"Payment Status: {payment_status}")
            
            # Note: trigger_local_webhook is async, but this sync function won't be called
            # from async context. If needed, should be refactored.
            
            time.sleep(2)
            
            # Check database status directly
            try:
                response = payments_table.get_item(Key={'payment_intent_id': payment_intent_id})
                item = response.get('Item')
                if item and item.get('payment_status') == 'completed':
                    print("Database status updated to 'completed'!")
                    return True
            except Exception as e:
                print(f"Error checking database status: {e}")
        
        if attempt < max_attempts - 1:
            print(f"   Stripe status: {payment_status or 'checking...'} - Retrying in 2 seconds... ({attempt + 1}/{max_attempts})")
            time.sleep(2)
    
    print("Payment was not completed within timeout")
    return False

def cleanup(payment_intent_id):
    try:
        payments_table.delete_item(Key={'payment_intent_id': payment_intent_id})
        print(f"Cleaned up test payment record: {payment_intent_id}")
    except:
        pass


# Note: /health endpoint is already defined above, no duplicate needed

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    logger.info(f"Webhook secret length: {len(STRIPE_WEBHOOK_SECRET)}")
    logger.info(f"Webhook secret: {STRIPE_WEBHOOK_SECRET[:15]}...")
    
    if not STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    try:
        if len(STRIPE_WEBHOOK_SECRET) < 20 or not sig_header:
            logger.warning("Using webhook without signature verification (local testing)")
            event = json.loads(payload.decode('utf-8'))
        else:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        if 'signature' in str(e).lower():
            logger.error(f"Invalid signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    event_type = event["type"]
    event_data = event["data"]["object"]
    
    logger.info(f"Received Stripe event: {event_type}")
    
    if event_type == "checkout.session.completed":
        await handle_payment_success(event_data)
    elif event_type == "checkout.session.expired":
        await handle_payment_expired(event_data)
    elif event_type == "payment_intent.payment_failed":
        await handle_payment_failed(event_data)
    else:
        logger.info(f"Unhandled event type: {event_type}")
    
    return JSONResponse({"status": "success", "event_type": event_type})

async def handle_payment_success(session_data: Dict[str, Any]):
    session_id = session_data.get("id")
    client_reference_id = session_data.get("client_reference_id")
    payment_intent_id = session_data.get("payment_intent")
    
    logger.info(f"Payment successful for session: {session_id}")
    
    if not client_reference_id:
        logger.warning(f"No client_reference_id found for session {session_id}")
        return
    
    try:
        response = payments_table.get_item(Key={"payment_intent_id": client_reference_id})
        payment_record = response.get("Item")
        
        if not payment_record:
            logger.warning(f"Payment record not found for payment_intent_id: {client_reference_id}")
            return
        
        payment_record["payment_status"] = "completed"
        payment_record["stripe_payment_intent"] = payment_intent_id
        payment_record["updated_at"] = datetime.utcnow().isoformat()
        payment_record["webhook_processed_at"] = datetime.utcnow().isoformat()
        
        payments_table.put_item(Item=payment_record)
        
        logger.info(f"Updated payment status to completed for {client_reference_id}")
        
    except Exception as e:
        logger.error(f"Failed to update payment record: {e}")

async def handle_payment_expired(session_data: Dict[str, Any]):
    session_id = session_data.get("id")
    client_reference_id = session_data.get("client_reference_id")
    
    logger.info(f"Payment session expired: {session_id}")
    
    if not client_reference_id:
        logger.warning(f"No client_reference_id found for expired session {session_id}")
        return
    
    try:
        response = payments_table.get_item(Key={"payment_intent_id": client_reference_id})
        payment_record = response.get("Item")
        
        if not payment_record:
            logger.warning(f"Payment record not found for payment_intent_id: {client_reference_id}")
            return
        
        payment_record["payment_status"] = "expired"
        payment_record["updated_at"] = datetime.utcnow().isoformat()
        payment_record["webhook_processed_at"] = datetime.utcnow().isoformat()
        
        payments_table.put_item(Item=payment_record)
        
        logger.info(f"Updated payment status to expired for {client_reference_id}")
        
    except Exception as e:
        logger.error(f"Failed to update expired payment record: {e}")

async def handle_payment_failed(payment_intent_data: Dict[str, Any]):
    payment_intent_id = payment_intent_data.get("id")
    
    logger.info(f"Payment failed for intent: {payment_intent_id}")
    
    try:
        response = payments_table.scan(
            FilterExpression="stripe_payment_intent = :intent_id",
            ExpressionAttributeValues={":intent_id": payment_intent_id}
        )
        
        items = response.get("Items", [])
        if not items:
            logger.warning(f"Payment record not found for intent: {payment_intent_id}")
            return
        
        payment_record = items[0]
        payment_record["payment_status"] = "failed"
        payment_record["updated_at"] = datetime.utcnow().isoformat()
        payment_record["webhook_processed_at"] = datetime.utcnow().isoformat()
        
        payments_table.put_item(Item=payment_record)
        
        logger.info(f"Updated payment status to failed for {payment_record['payment_intent_id']}")
        
    except Exception as e:
        logger.error(f"Failed to update failed payment record: {e}")
