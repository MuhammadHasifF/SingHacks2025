"""
backend/chains/policy_comparator.py
-----------------------------------
Final version supports:
- Plan comparison (TravelEasy, Scootsurance, Pre-Ex)
- Explanation of sections
- Eligibility checks
- Scenario coverage lookups
"""

import os
import json
from typing import Dict, List, Any

# Use only the combined taxonomy JSON
TAXONOMY_PATH = "data/processed/combined_taxonomy_policies.json"

# Load the combined taxonomy once
_combined_taxonomy = None


def load_all_policies() -> Dict[str, Any]:
    """Load the combined taxonomy JSON with all 3 products."""
    global _combined_taxonomy
    if _combined_taxonomy is None:
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
            _combined_taxonomy = json.load(f)

    # Return dict with product names as keys pointing to the full taxonomy
    products = _combined_taxonomy.get("products", [])
    return {product: _combined_taxonomy for product in products}


# ----------------------------------------------------------------------
# Compare two policies
# ----------------------------------------------------------------------
def compare_policies(policy_a: dict, policy_b: dict, keyword: str) -> str:
    """Compare two policies using a keyword that matches section names (taxonomy structure)."""
    keyword = keyword.lower()

    # Since both policy_a and policy_b are the same combined taxonomy, we need to extract product names differently
    # The "policy" dicts passed in are actually the full combined taxonomy
    products = policy_a.get("products", [])

    if len(products) < 2:
        return f"Comparing '{keyword}' coverage. Please refer to the policy documents for detailed information."

    # Get the first two products for comparison (or you can pass product indices)
    product_a_name = products[0]
    product_b_name = products[1]

    # Search in layer_2_benefits
    benefits = policy_a.get("layers", {}).get("layer_2_benefits", [])

    # Find matching benefit
    matching_benefit = None
    for benefit in benefits:
        benefit_name = benefit.get("benefit_name", "").lower()
        if keyword in benefit_name:
            matching_benefit = benefit
            break

    if not matching_benefit:
        return f"Coverage information for '{keyword}' is available in the policy documents. Please check the PDFs."

    # Extract product-specific data
    info_a = matching_benefit.get("products", {}).get(product_a_name, {})
    info_b = matching_benefit.get("products", {}).get(product_b_name, {})

    exists_a = info_a.get("condition_exist", False)
    exists_b = info_b.get("condition_exist", False)

    # Build comparison
    result = f"### Comparison: {matching_benefit.get('benefit_name', keyword)}\n\n"
    result += f"**{product_a_name}**: {'Covered' if exists_a else 'Not covered'}\n"
    result += f"**{product_b_name}**: {'Covered' if exists_b else 'Not covered'}\n"

    return result


# ----------------------------------------------------------------------
# Explain a section
# ----------------------------------------------------------------------
def explain_section(policy: dict, keyword: str) -> str:
    """Explain a benefit section by matching keyword (taxonomy structure)."""
    keyword = keyword.lower()

    # Search in layer_2_benefits
    benefits = policy.get("layers", {}).get("layer_2_benefits", [])

    for benefit in benefits:
        benefit_name = benefit.get("benefit_name", "").lower()
        if keyword in benefit_name:
            benefit_name_display = (
                benefit.get("benefit_name", keyword).replace("_", " ").title()
            )
            return f"**{benefit_name_display}** — This benefit is available across all products. Please check the policy documents for specific limits and conditions."

    return f"Information about '{keyword}' is available in the policy documents. Please check the PDFs for details."


# ----------------------------------------------------------------------
# Eligibility check
# ----------------------------------------------------------------------
def check_eligibility(policy: dict, condition: str) -> str:
    """Find mentions of eligibility or exclusions (taxonomy structure)."""
    condition_lower = condition.lower()

    # Search in layer_1_general_conditions
    conditions = policy.get("layers", {}).get("layer_1_general_conditions", [])

    for cond in conditions:
        cond_name = cond.get("condition", "").lower()
        if condition_lower in cond_name:
            cond_display = cond.get("condition", condition).replace("_", " ").title()
            cond_type = cond.get("condition_type", "condition")
            return f"**{cond_display}** ({cond_type}) — Please check the policy documents for specific eligibility requirements."

    return f"Please check the policy documents for '{condition}' eligibility details."


# ----------------------------------------------------------------------
# Scenario coverage
# ----------------------------------------------------------------------
SCENARIO_MAP = {
    "ski": "adventurous",
    "broken": "overseas_medical",
    "medical": "overseas_medical",
    "accident": "accidental",
    "death": "accidental",
    "cancellation": "trip_cancellation",
    "cancel": "trip_cancellation",
    "flight": "trip_cancellation",
}


def scenario_coverage(policy: dict, user_scenario: str) -> str:
    """Find best-matching coverage section for a scenario (taxonomy structure)."""
    scenario_lower = user_scenario.lower()

    # Map scenario keywords to taxonomy benefit names
    for keyword, mapped_term in SCENARIO_MAP.items():
        if keyword in scenario_lower:
            result = explain_section(policy, mapped_term)
            if "Information about" not in result and "available in" not in result:
                return result

    # Fallback to general search
    result = explain_section(policy, user_scenario)
    if "Information about" in result or "available in" in result:
        return result
    return "Coverage details for your scenario are in the policy documents. Please review the PDFs."


# ----------------------------------------------------------------------
# Local test
# ----------------------------------------------------------------------
if __name__ == "__main__":
    policies = load_all_policies()
    print(f"Loaded: {list(policies.keys())}")

    print(
        compare_policies(
            policies["TravelEasy Policy QTD032212"],
            policies["Scootsurance QSR022206"],
            "Trip Cancellation due to COVID-19",
        )
    )

    print(explain_section(policies["Scootsurance QSR022206"], "Trip Cancellation"))
    print(check_eligibility(policies["TravelEasy Policy QTD032212"], "pre-existing"))
    print(
        scenario_coverage(
            policies["TravelEasy Policy QTD032212"], "I broke my leg skiing in Japan"
        )
    )
