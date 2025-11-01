"""
backend/api.py
--------------
FastAPI bridge for the frontend. Exposes:
  - GET  /health
  - POST /chat
  - POST /upload
  - POST /upload_extract
"""

import os
import json
import traceback
from urllib.parse import quote as urlquote
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

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
from pydantic import BaseModel

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

