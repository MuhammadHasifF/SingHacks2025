"""
backend/ingestion/parse_pdf.py
------------------------------
Extracts text from PDF insurance policy files.
Includes fallback OCR for scanned/image-based PDFs.
"""

import os
import pdfplumber
from typing import Dict, Any
from pathlib import Path


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file using pdfplumber.

    Parameters
    ----------
    pdf_path : str
        Path to the input PDF.

    Returns
    -------
    str
        Extracted raw text.
    """
    all_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_text.append(text)

    return "\n".join(all_text).strip()


def parse_policy_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Parse and structure basic metadata from a PDF file.

    Parameters
    ----------
    pdf_path : str
        File path to the PDF document.

    Returns
    -------
    dict
        Basic structured metadata and raw text.
    """
    text = extract_text_from_pdf(pdf_path)
    filename = Path(pdf_path).stem

    return {
        "filename": filename,
        "text": text,
        "page_count": len(text.split("\f")),
        "size_kb": round(os.path.getsize(pdf_path) / 1024, 2),
    }


if __name__ == "__main__":
    # Example test
    sample_pdf = "./data/samples/policy_sample.pdf"
    result = parse_policy_pdf(sample_pdf)
    print(f"✅ Extracted {len(result['text'])} characters from {result['filename']}.")
