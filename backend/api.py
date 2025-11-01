"""
backend/api.py
--------------
FastAPI bridge for the frontend. Exposes:
  - POST /chat            (chatbot messages)
  - POST /upload          (raw file upload)
  - POST /upload_extract  (mock extraction summary)
"""

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os

# 🧠 Import internal modules
from backend.chains.conversational_agent import create_insurance_agent
from backend.chains.response_formatter import format_response
from backend.chains.intent import detect_intent
from backend.ingestion.parse_pdf import extract_trip_info

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

