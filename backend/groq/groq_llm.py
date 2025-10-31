"""
backend/groq/groq_llm.py
-------------------------
LangChain-compatible Groq model loader.
Uses the official `langchain_groq` integration.
"""

from langchain_groq import ChatGroq
from backend.config import GROQ_API_KEY


def get_groq_llm(model: str = "llama-3.3-70b-versatile", temperature: float = 0.3):
    """
    Returns a LangChain ChatGroq instance using the official connector.
    """
    return ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model=model,
        temperature=temperature,
    )
