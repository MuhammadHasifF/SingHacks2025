# backend/ingestion/pdf_loader.py
import fitz
import os

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a given PDF file."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return " ".join(text.split())
