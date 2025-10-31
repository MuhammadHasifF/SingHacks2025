"""
backend/chains/citation_helper.py
---------------------------------
Adds citations to chatbot responses.
"""

def add_citation(response_text: str, source: str) -> str:
    """Attach a citation footer."""
    return f"{response_text}\n\n📚 Source: {source}"
