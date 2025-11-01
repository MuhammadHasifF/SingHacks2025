"""
backend/api.py
--------------
FastAPI bridge for the frontend. Exposes POST /chat.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.chains.conversational_agent import create_insurance_agent
from backend.chains.response_formatter import format_response
from backend.chains.intent import detect_intent
from fastapi import UploadFile, File
import os


app = FastAPI(title="Insurance ScammerAPI", version="1.0")

# CORS for local dev / Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent once (holds in-memory chat history keyed by session_id)
agent = create_insurance_agent()

@app.post("/chat")
async def chat(request: Request):
    payload = await request.json()
    question = payload.get("question", "").strip()
    session_id = payload.get("session_id", "default")

    if not question:
        return format_response(
            text="Please ask a question (e.g., “Compare medical coverage”).",
            session_id=session_id,
            intent="general",
            citations=[],
        )

    try:
        # 1) Detect intent for UI metadata
        intent = detect_intent(question)

        # 2) Get routed + LLM formatted answer (already includes your JSON logic)
        answer_text = agent(session_id, question)

        # 3) Provide structured output (with a default citation label)
        return format_response(
            text=answer_text,
            session_id=session_id,
            intent=intent,
            citations=["MSIG TravelEasy / Pre-Ex / Scootsurance Official Policy Wordings (2025)"],
            meta={"model": "llama-3.3-70b-versatile"},
        )

    except Exception as e:
        # Graceful fallback for UI
        return format_response(
            text="Sorry, I ran into an error processing that. Please try again.",
            session_id=session_id,
            intent="error",
            citations=[],
            meta={"error": str(e)},
        )

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a PDF or image.
    Saves the file to /data/uploads for now (later DB/processing).
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return {"ok": True, "filename": file.filename, "path": file_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    
