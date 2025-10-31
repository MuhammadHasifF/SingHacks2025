"""
backend/chains/policy_comparator.py
-----------------------------------
Handles comparison logic for travel insurance policies using Groq LLM.
"""

from backend.groq.client import GroqClient

groq = GroqClient()

def compare_policies(plan_a: dict, plan_b: dict, category: str) -> str:
    """
    Compare two insurance policies based on a given benefit category.
    """
    prompt = f"""
    You are an expert insurance advisor. Compare the following two travel insurance plans 
    based on the category "{category}". Be concise, objective, and highlight which is better.

    ### Policy A
    {plan_a}

    ### Policy B
    {plan_b}

    Summarize key differences and clearly state which plan provides better coverage.
    """
    return groq.ask(prompt)
