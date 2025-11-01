# testmain.py

import os
import json
from pathlib import Path
import sys
# Add parent directory to path to ensure imports from src/ and config/ work
sys.path.append(str(Path(__file__).resolve().parent))

# Import the pipeline runner
from backend.ingestion.pipeline_ingest import run_ingestion

# Define test paths
OUTPUT_PATH = Path("data/outputs/structured_json/structured_insurance.json")

def test_ingestion_pipeline_end_to_end():
    """
    Performs an end-to-end test of the entire ingestion pipeline.
    """
    
    # 1. Ensure the necessary directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    print("--- STARTING PIPELINE TEST ---")
    
    # 2. Run the full pipeline
    try:
        run_ingestion()
    except Exception as e:
        print(f"❌ PIPELINE FAILED DURING EXECUTION: {e}")
        return

    # 3. Check if the output file was created
    assert OUTPUT_PATH.exists(), f"Output file not found at {OUTPUT_PATH}"
    
    # 4. Load and verify the content of the structured JSON
    with open(OUTPUT_PATH, 'r') as f:
        final_output = json.load(f)

    # Check general structure
    products = final_output.get('products', [])
    assert products is not None and len(products) > 0, "No products defined in the taxonomy."
    
    print("\n--- VERIFYING EXTRACTED DATA ---")
    
    # CRITICAL FIX: Use the correct benefit name from your taxonomy.json
    TARGET_BENEFIT_NAME = 'overseas_medical_expenses' 
    TARGET_PRODUCT = products[0] # Test against the first product found ('Product A')
    
    medical_benefit = None
    # Iterate through layer_2_benefits to find the one named 'overseas_medical_expenses'
    for item in final_output['layers'].get('layer_2_benefits', []):
        if item.get('benefit_name') == TARGET_BENEFIT_NAME:
            medical_benefit = item
            break
            
    # Assert that the item was actually found in the taxonomy structure
    assert medical_benefit is not None, f"❌ TEST FAILED: '{TARGET_BENEFIT_NAME}' benefit not found in the output structure."

    print(f"✅ '{TARGET_BENEFIT_NAME}' found in layer_2_benefits.")
    
    # Check that the LLM successfully attempted extraction for the target product
    product_entry = medical_benefit.get('products', {}).get(TARGET_PRODUCT)
    
    if product_entry and product_entry.get('condition_exist') is not None:
        print(f"✅ {TARGET_PRODUCT} Medical Expenses: condition_exist is present.")
        
        # Check for extracted parameters (assuming the target is to extract limit/excess)
        params = product_entry.get('parameters', {})
        if params.get('limit') and params.get('limit') != 'N/A':
            print(f"✅ {TARGET_PRODUCT} Medical Expenses Parameters extracted successfully (Found Limit).")
        else:
            print(f"⚠️ WARNING: {TARGET_PRODUCT} Medical Expenses limit extraction was unsuccessful or returned 'N/A'.")
    else:
        assert False, f"❌ {TARGET_PRODUCT} Medical Expenses: Extraction FAILED (could not find product entry or condition_exist in output)."


    print("\n--- TEST COMPLETE ---")
    print(f"Output saved to {OUTPUT_PATH}")

# Run the test function
if __name__ == "__main__":
    test_ingestion_pipeline_end_to_end()