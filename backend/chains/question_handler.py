"""
backend/chains/question_handler.py
----------------------------------
Routes user questions into specific categories (comparison, explanation, 
eligibility, scenario) and generates answers using Groq.
"""

from backend.groq.client import GroqClient
from backend.chains.policy_comparator import compare_policies

groq = GroqClient()

def handle_question(user_question: str, context_data: dict) -> str:
    """
    Analyze the user's question and determine the best response logic.
    """
    classifier_prompt = f"""
    Classify this question into one of: [comparison, explanation, eligibility, scenario]

    Question: "{user_question}"
    Respond with only one word.
    """
    question_type = groq.ask(classifier_prompt).lower()

    if "comparison" in question_type:
        return compare_policies(
            context_data.get("plan_a"), context_data.get("plan_b"), "medical coverage"
        )

    elif "explanation" in question_type:
        return explain_term(user_question, context_data)

    elif "eligibility" in question_type:
        return check_eligibility(user_question, context_data)

    elif "scenario" in question_type:
        return analyze_scenario(user_question, context_data)

    else:
        return "Sorry, I couldn’t determine what kind of question that is. Please rephrase."


def explain_term(user_question: str, context_data: dict) -> str:
    """Explain an insurance-related term."""
    prompt = f"""
    Explain the following insurance term clearly and simply:
    "{user_question}"
    Use context: {context_data}
    """
    return groq.ask(prompt)


def check_eligibility(user_question: str, context_data: dict) -> str:
    """Determine if a condition or case is covered under policy terms."""
    prompt = f"""
    Determine if the situation described is covered by the policy.
    Question: {user_question}
    Policy Context: {context_data}
    """
    return groq.ask(prompt)


def analyze_scenario(user_question: str, context_data: dict) -> str:
    """Assess whether the given scenario is covered by the policy."""
    prompt = f"""
    Analyze this scenario based on the policy context and coverage.
    Scenario: {user_question}
    Context: {context_data}
    """
    return groq.ask(prompt)
