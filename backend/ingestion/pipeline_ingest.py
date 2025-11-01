# backend/ingestion/pipeline_ingest.py

import os
import json
from pathlib import Path
from llama_index.llms.groq import Groq

# Import the core pipeline steps and configuration
from backend.ingestion.config.taxonomy_loader import MASTER_TAXONOMY, PRODUCT_NAMES
from backend.ingestion.extract_text import extract_text_from_pdfs
from backend.ingestion.classify_with_taxonomy import classify_document_chunks
from backend.ingestion.structure_with_schema import extract_parameters_for_item

# --- Configuration ---
# NOTE: Set your GROQ_API_KEY as an environment variable (e.g., export GROQ_API_KEY="...")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") 
# Assuming data/samples and data/outputs are relative to the project root
DATA_SAMPLES_DIR = Path("data/samples")
OUTPUT_FILE_PATH = Path("data/outputs/structured_json/structured_insurance.json")

# --- Model Selection ---
# RECOMMENDED REPLACEMENT FOR llama3-70b-8192 for complex extraction
EXTRACTION_MODEL = "llama-3.3-70b-versatile" 
# --- End Configuration ---

def run_ingestion():
    """
    The main ingestion pipeline: 
    Load PDFs -> Extract Text -> Classify (Batch) -> Structure -> Save Master JSON.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables. Please set it to proceed.")
        
    # Ensure output directories exist
    OUTPUT_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Start with a copy of the master taxonomy to fill
    final_structured_output = MASTER_TAXONOMY.copy()
    
    # Initialize the LLM for the final, complex extraction step
    llm = Groq(model=EXTRACTION_MODEL, temperature=0, api_key=GROQ_API_KEY)
    
    # Find all PDF files in the samples directory
    pdf_files = sorted(list(DATA_SAMPLES_DIR.glob("*.pdf")))
    
    if not pdf_files:
        print(f"No PDF files found in {DATA_SAMPLES_DIR}. Exiting.")
        return

    # Map product names from schema.json to the PDFs 
    file_to_product_map = {
        pdf.stem: product for pdf, product in zip(pdf_files, PRODUCT_NAMES)
    }

    print("\n--- Starting Master Ingestion Pipeline ---")
    print(f"Using Groq Model for Extraction: {EXTRACTION_MODEL}")

    # --- Process each PDF (Product) ---
    for pdf_path in pdf_files:
        product_key = file_to_product_map.get(pdf_path.stem, pdf_path.stem)
        print(f"\n--- Processing Document: {pdf_path.name} ({product_key}) ---")

        # Step 1: Extract Text
        full_document = extract_text_from_pdfs(pdf_path)
        if not full_document: continue
        
        # Step 2: Classify by Taxonomy (Batch Processing)
        # Note: This function uses the cheaper llama-3.1-8b-instant internally for token saving
        classified_nodes = classify_document_chunks(full_document, llm) 
        
        # --- Step 3: Structure via Schema (Iterative Extraction) ---
        print("--- Iterative Parameter Extraction ---")

        # Iterate through Layer 1 (General Conditions)
        for item in final_structured_output["layers"]["layer_1_general_conditions"]:
            extracted_data = extract_parameters_for_item(llm, item, classified_nodes, product_key)
            if extracted_data:
                item["products"][product_key] = extracted_data
                
        # Iterate through Layer 2 (Benefits)
        for item in final_structured_output["layers"]["layer_2_benefits"]:
            extracted_data = extract_parameters_for_item(llm, item, classified_nodes, product_key)
            if extracted_data:
                item["products"][product_key] = extracted_data

    # --- Step 4: Output Structured JSON ---
    with open(OUTPUT_FILE_PATH, 'w') as f:
        json.dump(final_structured_output, f, indent=2)
        
    print(f"\n--- Ingestion Complete ---")
    print(f"Final structured data saved to: {OUTPUT_FILE_PATH}")