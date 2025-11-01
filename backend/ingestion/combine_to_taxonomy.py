import os
import json
from copy import deepcopy

# Paths
TAXONOMY_PATH = "data/Taxonomy/Taxonomy_Hackathon.json"
PROCESSED_DIR = "data/processed"
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "combined_taxonomy_policies.json")

# Map your actual product filenames to taxonomy placeholders
PRODUCT_MAPPING = {
    "Product A": "TravelEasy Policy QTD032212",
    "Product B": "TravelEasy Pre-Ex Policy QTD032212-PX",
    "Product C": "Scootsurance QSR022206_updated"
}

def load_json(path):
    """Safely load JSON files."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Could not load {path}: {e}")
        return None

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    taxonomy = load_json(TAXONOMY_PATH)
    if not taxonomy:
        print("❌ Taxonomy file missing or invalid.")
        return

    # Create deep copy so we don’t modify the original
    combined = deepcopy(taxonomy)

    # Load processed product JSONs
    product_data = {}
    for product_name in PRODUCT_MAPPING.values():
        filename = f"{product_name}.json"
        file_path = os.path.join(PROCESSED_DIR, filename)
        if os.path.exists(file_path):
            product_data[product_name] = load_json(file_path)
            print(f"✅ Loaded: {filename}")
        else:
            print(f"⚠️ Missing file: {filename}")

    # Replace "Product A/B/C" placeholders in taxonomy
    combined["products"] = list(PRODUCT_MAPPING.values())
    combined["taxonomy_name"] = "Travel Insurance Product Taxonomy (Combined from PDFs)"

    for layer_name, layer_items in combined.get("layers", {}).items():
        for item in layer_items:
            products_section = item.get("products", {})
            new_products_section = {}

            for placeholder, actual_name in PRODUCT_MAPPING.items():
                new_products_section[actual_name] = {
                    "condition_exist": False,
                    "original_text": "",
                    "parameters": {}
                }

                # Try to find if the key term exists in that product’s data
                if actual_name in product_data:
                    data_str = json.dumps(product_data[actual_name]).lower()
                    keywords = [item.get("condition", ""), item.get("benefit_name", "")]
                    if any(k.lower() in data_str for k in keywords if k):
                        new_products_section[actual_name]["condition_exist"] = True
                        new_products_section[actual_name]["original_text"] = f"Found in document: {keywords}"

            # Replace product section in taxonomy
            item["products"] = new_products_section

    save_json(combined, OUTPUT_PATH)
    print(f"\n✅ Combined taxonomy JSON saved → {OUTPUT_PATH}")
    print("📦 All products aligned with taxonomy schema.")

if __name__ == "__main__":
    main()
