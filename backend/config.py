"""
backend/config.py
-----------------
Centralized configuration loader for environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# === Core Environment Variables ===
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
APP_ENV = os.getenv("APP_ENV", "local")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")

# === Validation ===
if not GROQ_API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY not set! Create your .env file.")
