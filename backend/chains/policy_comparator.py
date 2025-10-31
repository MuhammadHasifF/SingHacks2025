"""
backend/chains/policy_comparator.py
-----------------------------------
Final version for Hasif — supports:
- Plan comparison (TravelEasy, Scootsurance, Pre-Ex)
- Explanation of sections
- Eligibility checks
- Scenario coverage lookups
"""

import os
import json
from typing import Dict, List, Any

DATA_PATH = "data/processed"


# ----------------------------------------------------------------------
# Load all available policy JSONs
# ----------------------------------------------------------------------
def load_all_policies() -> Dict[str, Any]:
    """Load every JSON file from /data/processed/."""
    policies = {}
    for fname in os.listdir(DATA_PATH):
        if fname.endswith(".json"):
            path = os.path.join(DATA_PATH, fname)
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    plan_name = data.get("document_title", fname.replace(".json", ""))
                    policies[plan_name] = data
                except json.JSONDecodeError:
                    print(f"⚠️ Skipping invalid JSON: {fname}")
    return policies


# ----------------------------------------------------------------------
# Compare two policies
# ----------------------------------------------------------------------
def compare_policies(policy_a: dict, policy_b: dict, keyword: str) -> str:
    """Compare two policies using a keyword that matches section names."""
    keyword = keyword.lower()
    benefits_a = policy_a.get("data", {}).get("benefits", []) or []
    benefits_b = policy_b.get("data", {}).get("benefits", []) or []

    def find_section(benefits: List[dict]):
        for b in benefits:
            name = b.get("section_name", "").lower()
            if keyword in name:
                return b
        return None

    sec_a = find_section(benefits_a)
    sec_b = find_section(benefits_b)

    if not sec_a or not sec_b:
        return f"❌ Couldn’t find '{keyword}' in one or both policies."

    result = f"### Comparison for '{keyword.title()}'\n\n"
    result += f"🟩 **{policy_a['document_title']}**: {sec_a.get('section_name')}\n{sec_a.get('description','')}\n"
    result += f"\n🟦 **{policy_b['document_title']}**: {sec_b.get('section_name')}\n{sec_b.get('description','')}\n"

    # Add payout comparison
    for label, section in [("A", sec_a), ("B", sec_b)]:
        if "maximum_payouts" in section:
            result += f"\n**Plan {label} Maximum Payouts:**\n"
            for payout in section["maximum_payouts"]:
                result += f"- {payout.get('coverage_type')}: {payout.get('standard_plan', 'N/A')} / {payout.get('elite_plan','N/A')} / {payout.get('premier_plan','N/A')}\n"

    return result


# ----------------------------------------------------------------------
# Explain a section
# ----------------------------------------------------------------------
def explain_section(policy: dict, keyword: str) -> str:
    """Explain a benefit section by matching keyword."""
    keyword = keyword.lower()
    benefits = policy.get("data", {}).get("benefits", []) or []
    for b in benefits:
        if keyword in b.get("section_name", "").lower():
            return f"💡 **{b['section_name']}** — {b.get('description', 'No description found.')}"
    return f"❌ No section found for '{keyword}'. Try a different phrase."


# ----------------------------------------------------------------------
# Eligibility check
# ----------------------------------------------------------------------
def check_eligibility(policy: dict, condition: str) -> str:
    """Find mentions of eligibility or exclusions."""
    text_sections = policy.get("data", {}).get("general_important_conditions", []) or []
    for cond in text_sections:
        if condition.lower() in cond.get("description", "").lower():
            return f"✅ Mentioned in eligibility: {cond['description']}"
    return f"⚠️ '{condition}' not mentioned in eligibility — please verify with provider."


# ----------------------------------------------------------------------
# Scenario coverage
# ----------------------------------------------------------------------
SCENARIO_MAP = {
    "ski": "Adventurous activities cover",
    "broken leg": "Overseas medical expenses",
    "flight": "Trip Cancellation",
    "pet": "Domestic pets care",
}


def scenario_coverage(policy: dict, user_scenario: str) -> str:
    """Find best-matching coverage section for a scenario."""
    for key, mapped_section in SCENARIO_MAP.items():
        if key in user_scenario.lower():
            return explain_section(policy, mapped_section)
    return "❌ No related coverage found."


# ----------------------------------------------------------------------
# Local test
# ----------------------------------------------------------------------
if __name__ == "__main__":
    policies = load_all_policies()
    print(f"✅ Loaded: {list(policies.keys())}")

    print(compare_policies(
        policies["TravelEasy Policy QTD032212"],
        policies["Scootsurance QSR022206"],
        "Trip Cancellation due to COVID-19"
    ))

    print(explain_section(policies["Scootsurance QSR022206"], "Trip Cancellation"))
    print(check_eligibility(policies["TravelEasy Policy QTD032212"], "pre-existing"))
    print(scenario_coverage(policies["TravelEasy Policy QTD032212"], "I broke my leg skiing in Japan"))
