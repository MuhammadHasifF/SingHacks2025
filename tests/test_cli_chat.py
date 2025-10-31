"""
tests/test_cli_chat.py
---------------------------------
Interactive CLI tester for Hasif's Policy Intelligence System.
You can type any question and the system will respond using Groq logic.

Press Ctrl+C to exit anytime.
"""

import os
from dotenv import load_dotenv
from backend.chains.question_handler import handle_question
from backend.chains.policy_comparator import compare_policies
from backend.chains.citation_helper import add_citations

# Load API key
load_dotenv()

# Dummy structured policy data (like parsed JSONs)
plan_a = {
    "plan_name": "MSIG Basic Travel Plan",
    "medical_coverage": "Up to $100,000 for overseas medical expenses",
    "trip_cancellation": "Covers up to $2,000 for cancellations",
    "pre_existing": "Not covered"
}

plan_b = {
    "plan_name": "MSIG Premium Travel Plan",
    "medical_coverage": "Up to $500,000 for overseas medical expenses",
    "trip_cancellation": "Covers up to $5,000 for cancellations",
    "pre_existing": "Covered with conditions"
}

context_data = {
    "plan_a": plan_a,
    "plan_b": plan_b,
    "taxonomy": {
        "medical_coverage": "coverage of treatment and hospitalization abroad",
        "trip_cancellation": "reimbursement for trip interruptions or cancellations"
    }
}

def main():
    print("💬 Policy Intelligence CLI Tester (Hasif’s Module)")
    print("Type any insurance-related question to test logic.")
    print("Examples:")
    print(" - Which plan has better medical coverage?")
    print(" - What does trip cancellation mean?")
    print(" - Am I covered for pre-existing conditions?")
    print(" - If I break my leg skiing in Japan, am I covered?")
    print("--------------------------------------------------")

    while True:
        try:
            user_question = input("\n🧑‍💻 You: ").strip()
            if not user_question:
                continue

            # Route question
            answer = handle_question(user_question, context_data)

            # Add fake citations to simulate references
            sources = [
                {"filename": "MSIG_Basic.pdf", "page": 12, "snippet": "Overseas medical expenses section."},
                {"filename": "MSIG_Premium.pdf", "page": 9, "snippet": "Trip cancellation coverage details."}
            ]
            answer_with_refs = add_citations(answer, sources)

            print("\n🤖 JazzBot:", answer_with_refs)
        except KeyboardInterrupt:
            print("\n👋 Exiting chat. Goodbye!")
            break

if __name__ == "__main__":
    main()
