"""
backend/chains/question_handler.py
-----------------------------------
Detects question intent and routes it to the correct function.
"""

import re
from backend.chains.policy_comparator import compare_policies


def detect_intent(question: str) -> str:
    """
    Very basic intent detection based on keywords.

    Returns:
        "comparison" | "explanation" | "eligibility" | "scenario" | "general"
    """
    q = question.lower()

    if any(x in q for x in ["compare", "better", "vs", "difference"]):
        return "comparison"
    elif any(x in q for x in ["mean", "explain", "definition", "what is"]):
        return "explanation"
    elif any(x in q for x in ["covered", "cover", "eligibility", "pre-existing"]):
        return "eligibility"
    elif any(x in q for x in ["if i", "scenario", "situation", "accident", "break my"]):
        return "scenario"
    else:
        return "general"


def handle_question(question: str, plans_data: dict) -> str:
    """
    Routes question to specific function depending on detected intent.
    """

    intent = detect_intent(question)

    if intent == "comparison":
        # crude example: try to detect category
        if "medical" in question.lower():
            return compare_policies(plans_data["A"], plans_data["B"], "medical_coverage")
        elif "trip" in question.lower():
            return compare_policies(plans_data["A"], plans_data["B"], "trip_cancellation")
        else:
            return "Can you clarify what you want to compare?"
    elif intent == "explanation":
        return f"{question.capitalize()} usually refers to how an insurance policy defines and applies the relevant coverage or benefit."
    elif intent == "eligibility":
        return "Eligibility depends on pre-existing condition exclusions and age limits; please refer to the policy terms."
    elif intent == "scenario":
        return "Let’s check your scenario: coverage depends on trip purpose, country, and benefit limits."
    else:
        return "I can help you compare, explain, or check eligibility — try asking about a specific benefit."
