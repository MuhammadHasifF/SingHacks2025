# backend/ingestion/taxonomy_mapper.py
import json

def load_taxonomy(path="data/Taxonomy/Taxonomy_Hackathon.json"):
    """Load taxonomy schema."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_schema_prompt(taxonomy: dict) -> str:
    """
    Builds a prompt from taxonomy structure
    so the LLM knows the correct keys to extract.
    """
    formatted = json.dumps(taxonomy, indent=2)
    return f"""
You are an insurance document parser.
Extract information according to this schema:

{formatted}

Return ONLY valid JSON following this format.
If information is not found, use an empty string for that field.
"""
