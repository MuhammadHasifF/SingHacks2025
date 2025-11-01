# backend/ingestion/llama_structurer.py
import json
import re
import os
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


def init_llm():
    """Initialize Groq + Embeddings (reads API key from .env)."""
    load_dotenv()

    llm = Groq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY"),
    )
    embed = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    Settings.llm = llm
    Settings.embed_model = embed
    return llm


def extract_json_from_text(text):
    """Safely extract JSON from model output."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return None
    return None


def llm_structure_text(llm, text_chunk, schema_prompt):
    """Send one chunk to Groq for schema-based parsing."""
    response = llm.complete(f"{schema_prompt}\n\nDocument:\n{text_chunk}")
    parsed = extract_json_from_text(response.text)
    return parsed or {"raw_text": response.text}
