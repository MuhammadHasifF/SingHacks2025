"""
backend/chains/question_handler.py
-----------------------------------
Routes user queries to correct logic (comparison, explanation, eligibility, scenario).
"""

from backend.chains.policy_comparator import (
    load_all_policies,
    compare_policies,
    explain_section,
    check_eligibility,
    scenario_coverage
)

def handle_question(question: str) -> str:
    q = question.lower()
    policies = load_all_policies()
    travel = policies["TravelEasy Policy QTD032212"]
    scoot = policies["Scootsurance QSR022206_updated"]

    if any(k in q for k in ["compare", "better", "vs", "difference"]):
        # Comparison logic
        if "medical" in q:
            return compare_policies(travel, scoot, "overseas_medical_expenses")
        elif "trip" in q or "cancel" in q:
            return compare_policies(travel, scoot, "trip_cancellation")
        else:
            return "I can compare benefits like medical coverage or trip cancellation — which one?"

    elif any(k in q for k in ["mean", "explain", "what is"]):
        # Explanation
        if "trip" in q or "cancel" in q:
            return explain_section(scoot, "trip_cancellation")
        else:
            return explain_section(travel, "overseas_medical")

    elif any(k in q for k in ["cover", "covered", "eligibility", "pre-existing"]):
        # Eligibility
        return check_eligibility(travel, "pre-existing")

    elif any(k in q for k in ["if i", "scenario", "accident", "broke my", "ski"]):
        # Scenario
        return scenario_coverage(travel, q)

    else:
        return "I can compare plans, explain benefits, or check coverage. Try asking about 'trip cancellation' or 'medical coverage'."
