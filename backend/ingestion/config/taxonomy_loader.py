# config/taxonomy_loader.py

import json
from pathlib import Path
from typing import List, Dict, Any

# --- Robust Path Calculation ---
TAXONOMY_FILE_PATH = Path(__file__).resolve().parent / "schema.json"

def load_master_taxonomy() -> Dict[str, Any]:
    """Loads the master taxonomy JSON file."""
    try:
        with open(TAXONOMY_FILE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Re-raise with the computed path for debugging
        raise FileNotFoundError(f"Master Taxonomy file not found at {TAXONOMY_FILE_PATH}. Check file location.")
    except json.JSONDecodeError:
        raise ValueError(f"Error decoding JSON in {TAXONOMY_FILE_PATH}")

def load_and_get_classification_categories(taxonomy_data: Dict[str, Any]) -> List[str]:
    """Extracts all unique condition and benefit tags for the LLM classifier."""
    categories = set()
    layers = taxonomy_data.get("layers", {})
    
    # Layer 1: General Conditions (e.g., eligibility, exclusion)
    for item in layers.get("layer_1_general_conditions", []):
        condition_name = item.get("condition")
        condition_type = item.get("condition_type")
        if condition_name and condition_type:
            categories.add(f"{condition_type}:{condition_name}")
            
    # Layer 2: Benefits
    for item in layers.get("layer_2_benefits", []):
        benefit_name = item.get("benefit_name")
        condition_type = item.get("condition_type") # Use specific type if available
        if benefit_name:
            if condition_type:
                categories.add(f"{condition_type}:{benefit_name}")
            else:
                categories.add(f"benefit:{benefit_name}")

    return sorted(list(categories))

MASTER_TAXONOMY = load_master_taxonomy()
CLASSIFICATION_CATEGORIES = load_and_get_classification_categories(MASTER_TAXONOMY)
PRODUCT_NAMES = MASTER_TAXONOMY.get("products", [])