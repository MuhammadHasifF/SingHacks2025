"""
backend/utils/taxonomy_reader.py
---------------------------------
Read actual policy coverage amounts from sample JSON files.
"""

import json
import os
from typing import Dict, Any


def get_known_policy_coverage(product_name: str) -> Dict[str, Any]:
    """
    Return known coverage amounts from the policy PDFs as a fallback.
    These are manual entries based on actual policy documents.
    """
    known_coverage = {
        "TravelEasy Policy QTD032212": {
            "medical": "$100,000",
            "cancellation": "$5,000",
            "death_disablement": "$100,000",
            "price": "$42.50"
        },
        "TravelEasy Pre-Ex Policy QTD032212-PX": {
            "medical": "$100,000",
            "cancellation": "$4,000",
            "death_disablement": "$100,000",
            "price": "$49.90"
        },
        "Scootsurance QSR022206_updated": {
            "medical": "$70,000",
            "cancellation": "$1,000",
            "death_disablement": "$100,000",
            "dental": "$50,000",
            "travel_delay": "$600",
            "price": "$38.00"
        }
    }
    return known_coverage.get(product_name, {})


def load_policy_coverage(product_name: str) -> Dict[str, Any]:
    """
    Load actual coverage amounts for a product from sample JSON.
    
    Returns dict with medical, cancellation, death, dental, delay, and price.
    """
    # Try to load from known coverage first (most reliable)
    known_coverage = get_known_policy_coverage(product_name)
    if known_coverage:
        return known_coverage
    
    # If not found, try to extract from sample JSONs
    mapping = {
        "TravelEasy Policy QTD032212": "TravelEasy Policy QTD032212.json",
        "TravelEasy Pre-Ex Policy QTD032212-PX": "TravelEasy Pre-Ex Policy QTD032212-PX.json",
        "Scootsurance QSR022206_updated": "Scootsurance QSR022206_updated.json",
    }
    
    filename = mapping.get(product_name)
    if not filename:
        return {}
    
    sample_path = os.path.join("data/samples", filename)
    
    if not os.path.exists(sample_path):
        print(f"Sample file not found: {sample_path}")
        return {}
    
    try:
        with open(sample_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Extract coverage from the first item in the array
        if isinstance(data, list) and len(data) > 0:
            product_data = data[0]
        else:
            product_data = data
        
        # Initialize result with defaults
        result = {
            "medical": "$0",
            "cancellation": "$0",
            "price": "$0",
            "death_disablement": "$0",
            "dental": "$0",
            "travel_delay": "$0"
        }
        
        benefits = product_data.get("layers", {}).get("layer_2_benefits", [])
        
        for benefit in benefits:
            benefit_name = benefit.get("benefit_name", "").lower()
            products_section = benefit.get("products", {})
            
            # Get first product's parameters
            for prod_name, prod_data in products_section.items():
                if isinstance(prod_data, dict):
                    params = prod_data.get("parameters", {})
                    coverage_limit = params.get("coverage_limit", "")
                    if coverage_limit:
                        try:
                            amount = int(coverage_limit)
                            formatted = f"${amount:,}"
                            
                            # Map to field based on benefit name
                            if "medical" in benefit_name and "expenses" in benefit_name:
                                result["medical"] = formatted
                            elif "trip_cancellation" in benefit_name or "cancellation" in benefit_name:
                                result["cancellation"] = formatted
                            elif "accidental" in benefit_name and "death" in benefit_name:
                                result["death_disablement"] = formatted
                            elif "dental" in benefit_name:
                                result["dental"] = formatted
                            elif "travel_delay" in benefit_name:
                                result["travel_delay"] = formatted
                        except:
                            pass
                    break
        
        # Always add price from known coverage if not extracted
        if result.get("price") == "$0":
            known_coverage = get_known_policy_coverage(product_name)
            if known_coverage:
                result["price"] = known_coverage.get("price", "$0")
        
        return result
        
    except Exception as e:
        print(f"Error reading {sample_path}: {e}")
        return {}

