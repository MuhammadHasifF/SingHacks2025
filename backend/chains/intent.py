"""
backend/chains/intent.py
------------------------
Very lightweight keyword-based intent detection.
"""

def detect_intent(question: str) -> str:
    q = question.lower()

    if any(k in q for k in ["compare", "better", "vs", "difference"]):
        return "comparison"
    if any(k in q for k in ["what is", "mean", "explain", "definition"]):
        return "explanation"
    if any(k in q for k in ["pre-existing", "covered", "eligibility", "cover"]):
        return "eligibility"
    if any(k in q for k in ["if i", "scenario", "accident", "broke my", "ski"]):
        return "scenario"

    return "general"
