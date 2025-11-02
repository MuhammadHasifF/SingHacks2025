"""
backend/chains/citation_helper.py
---------------------------------
Appends clickable Markdown PDF citation links for insurance policy documents.
"""

import os
from urllib.parse import quote

# Base folder containing your PDFs
PDF_BASE_PATH = "data/Policy_Wordings"

# Mapping: internal policy name → actual file path
PDF_LINKS = {
    "TravelEasy Policy QTD032212": os.path.join(
        PDF_BASE_PATH, "TravelEasy Policy QTD032212.pdf"
    ),
    "TravelEasy Pre-Ex Policy QTD032212-PX": os.path.join(
        PDF_BASE_PATH, "TravelEasy Pre-Ex Policy QTD032212-PX.pdf"
    ),
    "Scootsurance QSR022206": os.path.join(
        PDF_BASE_PATH, "Scootsurance QSR022206_updated.pdf"
    ),
}


def add_citation(response_text: str, source_label: str = None) -> str:
    """
    Adds a Markdown-formatted citation block with clickable PDF links.

    Parameters
    ----------
    response_text : str
        The model's answer text.
    source_label : str, optional
        Label to show before the list (default = 'Sources').

    Returns
    -------
    str
        Formatted chatbot reply with clickable citations.
    """
    label = source_label or "Policy Documents"
    citation_block = f"\n\n**{label}:**\n"

    for title, path in PDF_LINKS.items():
        # Convert local path to API endpoint with URL encoding
        filename = os.path.basename(path)
        pdf_url = f"http://127.0.0.1:8000/policy_pdf/{quote(filename)}"
        citation_block += f"- [{title} (PDF)]({pdf_url})\n"

    return response_text + citation_block
