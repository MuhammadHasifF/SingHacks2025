# backend/ingestion/parse_pdf.py
"""
Temporary mock extractor for Block 3.
When Mahesh/Noah finish OCR, swap this function’s body to use real parsing.
"""

from pathlib import Path

SUPPORTED = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}


def extract_trip_info(file_path: str) -> dict:
    """
    Return a mocked trip info dict for UI wiring & testing.

    Parameters
    ----------
    file_path : str
        Absolute or relative path to the uploaded file.

    Returns
    -------
    dict
        { traveler_name, destination, dates, trip_cost }
    """
    ext = Path(file_path).suffix.lower()
    if ext not in SUPPORTED:
        return {"error": f"Unsupported file type: {ext}"}

    # NOTE: replace this block with real OCR/text parsing later.
    # You can add filename-based heuristics during testing if helpful.
    return {
        "traveler_name": "John Doe",
        "destination": "Japan",
        "dates": "2025-12-01 → 2025-12-10",
        "trip_cost": 2500,
    }
