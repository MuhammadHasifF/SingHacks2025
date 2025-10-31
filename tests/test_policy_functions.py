"""
tests/test_policy_functions.py
---------------------------------
Quick manual test for Hasif's policy comparison, explanation, 
eligibility, and scenario logic.
"""

import os
from dotenv import load_dotenv

# Load your API key from .env
load_dotenv()

from backend.chains.question_handler import handle_question
from backend.chains.policy_comparator import compare_policies
from backend.chains.citation_helper import add_citations

# Dummy policy data
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
    "taxonomy": {"medical_coverage": "coverage of treatment and hospitalization abroad"}
}

# 🔹 Test 1 — Comparison
print("\n🧩 TEST 1: Compare Medical Coverage")
response = compare_policies(plan_a, plan_b, "medical_coverage")
print("Response:\n", response)

# 🔹 Test 2 — Explanation
print("\n🧩 TEST 2: Explain Term")
question = "What does trip cancellation mean?"
response = handle_question(question, context_data)
print("Response:\n", response)

# 🔹 Test 3 — Eligibility
print("\n🧩 TEST 3: Eligibility Question")
question = "Am I covered for pre-existing conditions?"
response = handle_question(question, context_data)
print("Response:\n", response)

# 🔹 Test 4 — Scenario
print("\n🧩 TEST 4: Scenario Analysis")
question = "If I break my leg skiing in Japan, am I covered?"
response = handle_question(question, context_data)
print("Response:\n", response)

# 🔹 Test 5 — Add Citations
print("\n🧩 TEST 5: Citation Attachment")
sources = [
    {"filename": "MSIG_Basic.pdf", "page": 12, "snippet": "Overseas medical expenses up to $100,000."},
    {"filename": "MSIG_Premium.pdf", "page": 9, "snippet": "Medical coverage includes hospitalization up to $500,000."}
]
final_answer = add_citations("Premium plan offers higher coverage.", sources)
print(final_answer)
