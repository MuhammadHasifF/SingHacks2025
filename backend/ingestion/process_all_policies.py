# backend/ingestion/process_all_policies.py
import os
import json
from backend.ingestion.pdf_loader import extract_text_from_pdf
from backend.ingestion.taxonomy_mapper import load_taxonomy, build_schema_prompt
from backend.ingestion.llama_structurer import init_llm, llm_structure_text

DATA_DIR = "data/Policy_Wordings"
OUTPUT_DIR = "data/processed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

MAX_CHARS = 3000  # text chunk size

def process_pdf(file_path, llm, schema_prompt):
    text = extract_text_from_pdf(file_path)
    chunks = [text[i:i + MAX_CHARS] for i in range(0, len(text), MAX_CHARS)]
    results = []
    for i, chunk in enumerate(chunks):
        print(f"🔹 Processing chunk {i+1}/{len(chunks)}...")
        result = llm_structure_text(llm, chunk, schema_prompt)
        results.append(result)
    return results

def main():
    taxonomy = load_taxonomy()
    schema_prompt = build_schema_prompt(taxonomy)
    llm = init_llm()

    for file in os.listdir(DATA_DIR):
        if not file.endswith(".pdf"):
            continue
        pdf_path = os.path.join(DATA_DIR, file)
        print(f"\n📄 Processing: {file}")
        structured_data = process_pdf(pdf_path, llm, schema_prompt)

        out_path = os.path.join(OUTPUT_DIR, file.replace(".pdf", ".json"))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved structured JSON → {out_path}")

if __name__ == "__main__":
    main()
