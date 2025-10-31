"""
backend/chains/policy_comparator.py
-----------------------------------
Compare insurance policy data such as medical, cancellation, and coverage amounts.
"""

from typing import Dict, Any


def compare_policies(plan_a: Dict[str, Any], plan_b: Dict[str, Any], category: str) -> str:
    """
    Compare two plans within a specific coverage category (e.g., 'medical_coverage').

    Args:
        plan_a: Dict containing key-value policy data for Plan A.
        plan_b: Dict containing key-value policy data for Plan B.
        category: The coverage field to compare (e.g., 'medical_coverage').

    Returns:
        str: Human-readable comparison summary.
    """

    a_val = plan_a.get(category, "N/A")
    b_val = plan_b.get(category, "N/A")

    if a_val == "N/A" or b_val == "N/A":
        return f"I couldn’t find comparable data for {category}."

    # Example: numerical or qualitative comparison
    if isinstance(a_val, (int, float)) and isinstance(b_val, (int, float)):
        better = "A" if a_val > b_val else "B"
        diff = abs(a_val - b_val)
        return f"Plan {better} offers higher {category.replace('_', ' ')} coverage (difference: {diff:,})."
    else:
        return f"Plan A: {a_val} vs Plan B: {b_val} for {category.replace('_', ' ')}."
