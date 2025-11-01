"""
backend/chains/response_formatter.py
------------------------------------
Small helper to produce a consistent JSON payload for the frontend.
"""

from typing import List, Dict, Any

def format_response(
    text: str,
    session_id: str,
    intent: str = "general",
    citations: List[str] | None = None,
    meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Return a normalized response object the UI can always rely on.
    """
    return {
        "text": text,
        "intent": intent,
        "citations": citations or [],
        "session_id": session_id,
        "meta": meta or {},
    }
