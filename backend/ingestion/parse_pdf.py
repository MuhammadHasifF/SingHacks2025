# import os
# import json
# import fitz
# import re
# import time
# from llama_index.llms.groq import Groq
# from llama_index.embeddings.huggingface import HuggingFaceEmbedding
# from llama_index.core import Settings

# # --------------------------
# # Configuration
# # --------------------------
# DATA_DIR = "data/samples"
# OUTPUT_DIR = "output"
# os.makedirs(OUTPUT_DIR, exist_ok=True)

# os.environ["GROQ_API_KEY"] = "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"

# SCHEMA_FILE = "backend/ingestion/schema.json"

# MAX_CHARS = 3000  # Large chunks (~750 tokens)
# SLEEP_BETWEEN_CALLS = 0.5  # Prevent rate limit

# with open(SCHEMA_FILE, "r") as f:
#     schema_json = f.read()

    # llm = Groq(model="llama-3.3-70b-versatile", temperature=0.3)
    # embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    # Settings.llm = llm
    # Settings.embed_model = embed_model

# SCHEMA_PROMPT = f"""
# You are a data extraction assistant.
# Extract all relevant information from this travel insurance document.
# Return only valid JSON following this schema exactly:

# {schema_json}

# If a field is missing, leave it empty.
# """

# def extract_text_from_pdf(pdf_path):
#     doc = fitz.open(pdf_path)
#     text = ""
#     for page in doc:
#         text += page.get_text("text")
#     return text

# def extract_json_from_text(text):
#     try:
#         return json.loads(text)
#     except json.JSONDecodeError:
#         match = re.search(r"\{.*\}", text, re.DOTALL)
#         if match:
#             try:
#                 return json.loads(match.group())
#             except json.JSONDecodeError:
#                 return None
#         return None

# # --------------------------
# # Process PDFs
# # --------------------------
# documents = [f for f in os.listdir(DATA_DIR) if f.endswith('.pdf')]

# for doc_name in documents:
#     product_name = doc_name.replace(".pdf", "")
#     pdf_path = os.path.join(DATA_DIR, doc_name)
#     print(f"\nProcessing {product_name}...")

#     # 1️⃣ Extract text from PDF
#     text = extract_text_from_pdf(pdf_path)

#     # 2️⃣ Split into chunks
#     chunks = [text[i:i+MAX_CHARS] for i in range(0, len(text), MAX_CHARS)]
#     chunk_results = []

#     # 3️⃣ Extract JSON per chunk
#     for i, chunk in enumerate(chunks):
#         print(f" → Processing chunk {i+1}/{len(chunks)}")
#         response = llm.complete(f"{SCHEMA_PROMPT}\n\nDocument part:\n{chunk}")
#         parsed_json = extract_json_from_text(response.text) or {"raw_output": response.text}
#         chunk_results.append(parsed_json)
#         time.sleep(SLEEP_BETWEEN_CALLS)

#     # 4️⃣ Merge all chunks if needed
#     if len(chunk_results) == 1:
#         final_json = chunk_results[0]
#     else:
#         merge_prompt = f"""
# Merge the following JSON fragments into one JSON following this schema exactly:
# {schema_json}

# Fragments:
# {json.dumps(chunk_results)}
# """
#         merged_response = llm.complete(merge_prompt)
#         final_json = extract_json_from_text(merged_response.text) or {"raw_output": merged_response.text}
#         time.sleep(SLEEP_BETWEEN_CALLS)

#     # 5️⃣ Save pretty JSON
#     output_path = os.path.join(OUTPUT_DIR, f"{product_name}.json")
#     with open(output_path, "w") as f:
#         json.dump(final_json, f, indent=2, ensure_ascii=False)

#     print(f"✅ Saved {output_path}")


# structure.py
import pandas as pd
import os
import json
from pathlib import Path
# from pydantic import BaseModel, Field, ValidationError 
from groq import Groq as GroqClient 
from llama_index.core import load_index_from_storage, StorageContext, Settings 
from llama_index.core.embeddings import resolve_embed_model 

# --- 1. Define schema source ---
STORAGE_DIR = "backend/ingestion/llama_storage"
STORAGE_DIR_ABS = os.path.abspath(STORAGE_DIR)
SUMMARY_FILE_PATH = 'output/parsed/master_insurance_summary.csv'
SCHEMA_FILE_PATH = 'backend/ingestion/schema.json' 
FINAL_GENAI_OUTPUT = 'output/structured/final_genai_structured_output_groq_optimized.json'

os.environ["GROQ_API_KEY"] = "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"

# --- 2. Initialize Groq Client and Define Prompt Function ---
groq_client_direct = GroqClient() 
# Changed model back to the smaller, faster one to fit within limits
GROQ_MODEL = "llama-3.3-70b-versatile" 

def process_with_genai_and_schema(df, index, schema_string):
    structured_genai_output = []
    
    # Configure the retriever to limit context (e.g., top_k=2 instead of default 4)
    # This reduces prompt size
    retriever = index.as_retriever(similarity_top_k=2) 
    
    system_prompt = f"""
    You are an expert insurance data extractor. Analyze the policy data and output a JSON object that strictly adheres to the schema provided. 
    Use the provided SCHEMA. Return ONLY the JSON object.
    """
    
    for index_val, row in df.iterrows():
        print(f"[STRUCTURING] Processing record from file: {row.get('Source_File', 'N/A')}")
        input_text = f"Policy Number: {row['Policy_Number']}, Limit: {row['Coverage_Limit']}, Deductible: {row['Deductible']}, Exclusions: {row['Exclusions']}."
        
        try:
            # Retrieve limited context using the optimized retriever
            retrieved_nodes = retriever.retrieve(f"What context can you provide for policy {row['Policy_Number']}?")
            context_text = "\n".join([node.get_content() for node in retrieved_nodes])

            # Keep the prompt concise
            augmented_prompt = f"{input_text}\nContext: {context_text}\nSchema:\n{schema_string}"
            
            response = groq_client_direct.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": augmented_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            json_string = response.choices.message.content.strip()
            json_object = json.loads(json_string) 
            structured_genai_output.append(json_object)
            
        except Exception as e:
            print(f"  [GenAI Error] Failed for {row.get('Source_File', 'N/A')}: {e}")

    return structured_genai_output

# ... (rest of the main execution block remains the same, loading schema and running function) ...
Settings.embed_model = resolve_embed_model("local:BAAI/bge-small-en-v1.5")
print(f"Set global embedding model to BAAI/bge-small-en-v1.5")
print(f"Using LlamaIndex storage directory: {STORAGE_DIR_ABS}")


# Load the schema file first
try:
    with open(SCHEMA_FILE_PATH, 'r') as f:
        custom_schema_data = json.load(f)
        schema_string = json.dumps(custom_schema_data, indent=4) 
    print(f"Successfully loaded schema from {SCHEMA_FILE_PATH}")

except FileNotFoundError:
    print(f"ERROR: Schema file '{SCHEMA_FILE_PATH}' not found. Please create it.")
    exit()
except json.JSONDecodeError:
    print(f"ERROR: Could not decode JSON from '{SCHEMA_FILE_PATH}'. Check file format.")
    exit()


if not os.path.exists(STORAGE_DIR_ABS) or not os.path.isdir(STORAGE_DIR_ABS):
    print(f"ERROR: LlamaIndex storage directory '{STORAGE_DIR_ABS}' not found. Please run extract.py first.")

elif os.path.exists(STORAGE_DIR_ABS) and os.path.isdir(STORAGE_DIR_ABS):
    try:
        print("\n[LLAMA] Loading LlamaIndex storage...")
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR_ABS)
        index = load_index_from_storage(storage_context)
        print("[LLAMA] Storage loaded successfully.")
        
        df_master = pd.read_csv(SUMMARY_FILE_PATH)
        if df_master.empty:
            print("No data in master file.")
        else:
            final_structured_results = process_with_genai_and_schema(df_master, index, schema_string)
            with open(FINAL_GENAI_OUTPUT, 'w', encoding='utf-8') as f:
                json.dump(final_structured_results, f, indent=4)
            print(f"\n[STRUCTURED] Final Groq structured output saved to '{FINAL_GENAI_OUTPUT}'")
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
else:
    print(f"Summary file '{SUMMARY_FILE_PATH}' not found or is empty. Please run parse.py first.")

