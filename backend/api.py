"""
backend/api.py
--------------
FastAPI bridge for the frontend. Exposes:
  - POST /chat            (chatbot messages)
  - POST /upload          (raw file upload)
  - POST /upload_extract  (mock extraction summary)
"""

from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

# 🧠 Import internal modules
from backend.chains.conversational_agent import create_insurance_agent
from backend.chains.response_formatter import format_response
from backend.chains.intent import detect_intent
from backend.ingestion.parse_pdf import extract_trip_info


import stripe
import boto3
from datetime import datetime
import uuid
from dotenv import load_dotenv
import requests
import time
import logging
import json
from typing import Dict, Any


# ---------------------------------------------------------------------------- #
# ⚙️ FastAPI Initialization
# ---------------------------------------------------------------------------- #
app = FastAPI(title="Insurance Scammer API", version="1.0")

# CORS (for Streamlit localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------- #
# 🤖 Chatbot Endpoint (/chat)
# ---------------------------------------------------------------------------- #
agent = create_insurance_agent()  # in-memory singleton

@app.post("/chat")
async def chat(request: Request):
    """Handle user chatbot questions."""
    payload = await request.json()
    question = payload.get("question", "").strip()
    session_id = payload.get("session_id", "default")

    if not question:
        return format_response(
            text="Please ask a question (e.g., 'Compare medical coverage').",
            session_id=session_id,
            intent="general",
            citations=[],
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
        return format_response(
            text="Sorry, I ran into an error processing that. Please try again.",
            session_id=session_id,
            intent="error",
            citations=[],
            meta={"error": str(e)},
        )

# ---------------------------------------------------------------------------- #
# 📎 Upload Endpoints
# ---------------------------------------------------------------------------- #
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a PDF or image file.
    Saves the file to /data/uploads (temporary storage).
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        return {"ok": True, "filename": file.filename, "path": file_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/upload_extract")
async def upload_and_extract(file: UploadFile = File(...)):
    """
    Save uploaded PDF or image and return a mock trip + quote summary.
    Later this will use real OCR + plan logic.
    """
    try:
        save_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())

        # 🧠 Mock trip info (pretend extracted)
        trip = {
            "traveler_name": "John Doe",
            "destination": "Japan",
            "dates": "2025-12-01 to 2025-12-10",
            "trip_cost": 2500,
        }

        # 💸 Mock quote summary (using your 3 policies)
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

        return {
            "ok": True,
            "filename": file.filename,
            "path": save_path,
            "trip": trip,
            "quotes": quotes,
        }

    except Exception as e:
        return {"ok": False, "error": str(e)}
    
# ---------------------------------------------------------------------------- #
# Stripe Endpoint
# ---------------------------------------------------------------------------- #

load_dotenv()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY

dynamodb = boto3.resource(
    'dynamodb',
    region_name='ap-southeast-2',
    endpoint_url='http://localhost:8000',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

payments_table = dynamodb.Table('lea-payments-local')

# API to create payment intent
@app.post("/payment-intent")
async def create_payment_intent(request: Request):
    payload = await request.json()
    payment_intent_id = f"test_payment_{uuid.uuid4().hex[:12]}"
    user_id =  "user_" + str(payload.get("session_user_id"))
    quote_id = f"quote_{uuid.uuid4().hex[:8]}"
    amount = payload.get("purchase_amount")
    product_name = payload.get("product_name")

    print("Creating payment record in DynamoDB with 'pending' status")
    
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
        print(f"Payment record created with ID: {payment_intent_id}")
        return {
            'payment_intent_id': payment_intent_id,
            'payment_status': 'pending',
            'user_id': user_id
        }
    except Exception as e:
        print(f"Failed to create payment record: {e}")


#API to trigger stripe
@app.post('/stripe-checkout')
async def create_stripe_checkout(request: Request):
    print("Creating Stripe Checkout Session")
    payload = await request.json()

    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'sgd',
                    'unit_amount': payload.get("purchase_amount"),
                    'product_data': {
                        'name': payload.get("product_name"),
                        'description': 'Travel Insurance Policy',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'http://localhost:8085/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url='http://localhost:8085/cancel',
            client_reference_id=payload.get("payment_intent_id"),
        )
        
        payments_table.update_item(
            Key={'payment_intent_id': payload.get("payment_intent_id")},
            UpdateExpression='SET stripe_session_id = :sid',
            ExpressionAttributeValues={':sid': checkout_session.id}
        )
        
        print("Stripe Checkout Session created")
        print(f"Session ID: {checkout_session.id}")
        return checkout_session
        
    except Exception as e:
        print(f"Failed to create Stripe session: {e}")

@app.get('/payment-status/{payment_intent_id}')
async def check_payment_status(payment_intent_id):
    try:
        response = payments_table.get_item(Key={'payment_intent_id': payment_intent_id})
        item = response.get('Item')
        if item:
            return item.get('payment_status', 'unknown')
        return None
    except Exception as e:
        print(f"Failed to check payment status: {e}")
        return None

# @app.get('/payment-status/{session_id}')
async def check_stripe_payment_status(session_id):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session.payment_status, session
    except Exception as e:
        print(f"Failed to check Stripe status: {e}")
        return None, None

@app.post('/trigger-webhook')
async def trigger_local_webhook(request: Request):
    payload = request.json()
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
    print(4, "Checking payment status on Stripe")
    print("Polling Stripe API for payment completion...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        payment_status, session_data = check_stripe_payment_status(session_id)
        
        if payment_status == 'paid':
            print("Payment confirmed on Stripe!")
            print(f"Payment Status: {payment_status}")
            
            trigger_local_webhook(session_data)
            
            time.sleep(2)
            
            db_status = check_payment_status(payment_intent_id)
            if db_status == 'completed':
                print("Database status updated to 'completed'!")
                return True
            else:
                print(f"Database status: {db_status} (waiting for webhook processing...)")
                time.sleep(2)
                db_status = check_payment_status(payment_intent_id)
                if db_status == 'completed':
                    print("Database status confirmed as 'completed'!")
                    return True
        
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


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stripe-webhook")

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
DYNAMODB_PAYMENTS_TABLE = os.getenv("DYNAMODB_PAYMENTS_TABLE", "lea-payments-local")
DDB_ENDPOINT = os.getenv("DDB_ENDPOINT")

if DDB_ENDPOINT:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION, endpoint_url=DDB_ENDPOINT)
else:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

payments_table = dynamodb.Table(DYNAMODB_PAYMENTS_TABLE)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "stripe-webhook"}

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
    
    return JSONResponse({"status": "success"})

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