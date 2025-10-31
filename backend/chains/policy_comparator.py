"""
backend/chains/policy_comparator.py
-----------------------------------
Compares real insurance plan JSONs from /data/processed/.
"""

import os, json

DATA_PATH = "data/processed"

def load_all_policies() -> dict:
    """Load all available policy JSONs."""
    policies = {}
    for fname in os.listdir(DATA_PATH):
        if fname.endswith(".json"):
            with open(os.path.join(DATA_PATH, fname), "r") as f:
                data = json.load(f)
                plan_name = data.get("plan_name", fname.replace(".json", ""))
                policies[plan_name] = data
    return policies


def summarize_policy(plan: dict) -> str:
    """Summarize a policy’s benefits for debugging or quick view."""
    if not plan:
        return "❌ Policy not found."
    benefits = plan.get("data", {}).get("benefits", [])
    lines = []
    for b in benefits[:5]:  # just show first few
        lines.append(f"- {b.get('section_name')}")
    return f"✅ {plan.get('plan_name', 'Unnamed')} includes:\n" + "\n".join(lines)


def compare_policies(policy_a: dict, policy_b: dict, benefit_name: str) -> str:
    """Compare two policies for a specific benefit section."""
    a_sections = {b["section_name"].lower(): b for b in policy_a["data"]["benefits"]}
    b_sections = {b["section_name"].lower(): b for b in policy_b["data"]["benefits"]}

    benefit = benefit_name.lower()
    a_benefit = a_sections.get(benefit)
    b_benefit = b_sections.get(benefit)

    if not a_benefit or not b_benefit:
        return f"❌ Couldn’t find '{benefit_name}' in one or both policies."

    result = f"### Comparison for {benefit_name}\n\n"
    result += f"**{policy_a['plan_name']}**: {a_benefit.get('description', '')}\n"
    result += f"**{policy_b['plan_name']}**: {b_benefit.get('description', '')}\n"

    # Add payout table info if available
    if "maximum_payouts" in a_benefit:
        result += "\n\n**Maximum Payouts (Plan A)**:\n"
        for payout in a_benefit["maximum_payouts"]:
            result += f"- {payout.get('coverage_type')}: {payout.get('standard_plan', 'N/A')}\n"
    if "maximum_payouts" in b_benefit:
        result += "\n\n**Maximum Payouts (Plan B)**:\n"
        for payout in b_benefit["maximum_payouts"]:
            result += f"- {payout.get('coverage_type')}: {payout.get('standard_plan', 'N/A')}\n"

    return result


if __name__ == "__main__":
    all_policies = load_all_policies()
    for name, policy in all_policies.items():
        print(summarize_policy(policy))
