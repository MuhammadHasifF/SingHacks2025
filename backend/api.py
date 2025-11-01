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
import traceback
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# 🧠 Internal modules
from backend.chains.conversational_agent import create_insurance_agent
from backend.chains.response_formatter import format_response
from backend.chains.intent import detect_intent

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
async def upload_and_extract(file: UploadFile = File(...)):
    try:
        save_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())

        trip = {
            "traveler_name": "John Doe",
            "destination": "Japan",
            "dates": "2025-12-01 to 2025-12-10",
            "trip_cost": 2500,
        }

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
