"""
backend/chains/citation_helper.py
---------------------------------
Adds reference citations (from PDFs or Chroma metadata)
to chatbot responses for transparency.
"""

def add_citations(answer: str, sources: list) -> str:
    """
    Append citation information to an AI answer.

    Parameters
    ----------
    answer : str
        AI-generated text.
    sources : list
        List of dicts with 'filename', 'page', and 'snippet'.

    Returns
    -------
    str
        Answer text with formatted citations appended.
    """
    if not sources:
        return answer

    citation_text = "\n\n📚 **References:**\n"
    for src in sources:
        citation_text += f"- {src.get('filename', 'Unknown File')} (Page {src.get('page', '?')}): “{src.get('snippet', '')}”\n"

    return answer + citation_text
