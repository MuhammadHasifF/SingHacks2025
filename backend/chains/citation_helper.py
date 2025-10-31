"""
backend/chains/citation_helper.py
---------------------------------
Handles attaching source citations or links to responses.
"""

from typing import List, Dict


def add_citations(response: str, sources: List[Dict[str, str]]) -> str:
    """
    Adds citation references to an AI response.

    Args:
        response: Model-generated text.
        sources: List of dicts with {"text": ..., "source": ...}.

    Returns:
        str: Response text with appended citation lines.
    """
    if not sources:
        return response

    citations = "\n\n📚 Sources:\n"
    for s in sources:
        text = s.get("text", "")
        src = s.get("source", "")
        citations += f" - {src}: \"{text[:60]}...\"\n"

    return response + citations
