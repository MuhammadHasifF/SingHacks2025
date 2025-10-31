"""
backend/config.py
-----------------
Loads environment variables and exposes configuration constants
for the entire backend (used by Groq, Chroma, FastAPI, etc.).
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === Core Configurations ===
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
APP_ENV = os.getenv("APP_ENV", "local")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")

# === Validation ===
if not GROQ_API_KEY:
    raise RuntimeError("⚠️ GROQ_API_KEY is not set. Please configure your .env file.")
