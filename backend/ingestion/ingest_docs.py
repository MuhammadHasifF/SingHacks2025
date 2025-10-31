# backend/ingestion/ingest_docs.py
import os
import chromadb
from dotenv import load_dotenv

from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    Document  # Import Document
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.core import Settings
from llama_index.program.openai import OpenAIPydanticProgram

# 1. Import your new Taxonomy/Schema
from backend.ingestion.metadata_schema import PolicyDetails 

# Load API keys from .env
load_dotenv()

def main():
    # --- 1. CONFIGURE MODELS ---
    print("Setting up models...")
    Settings.llm = Groq(model="llama3-8b-8192")
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )

    # --- 2. SET UP THE EXTRACTION PROGRAM ---
    # This program links your LLM (Groq) to your Pydantic schema
# NEW CODE
# We use OpenAIPydanticProgram because Groq is OpenAI-compatible
    program = OpenAIPydanticProgram.from_defaults(
    output_class=PolicyDetails,
    llm=Settings.llm,
    prompt_template_str=(
        "Please extract the following information from the provided document:\n"
        "{input_text}"
    ),
    verbose=True
)

    # --- 3. LOAD RAW DOCUMENTS ---
    pdf_folder_path = "./data/samples" # Make sure this folder exists!
    print(f"Loading documents from {pdf_folder_path}...")
    # Load the docs one by one
    reader = SimpleDirectoryReader(input_dir=pdf_folder_path)
    raw_docs = reader.load_data()
    print(f"Loaded {len(raw_docs)} raw document(s).")

    # --- 4. NORMALIZE AND EXTRACT METADATA (The new step) ---
    print("Normalizing data into taxonomy structure...")
    normalized_documents = []
    
    for doc in raw_docs:
        # Run the extraction program on the text
        try:
            extracted_data = program(input_text=doc.text)
            
            # Convert the Pydantic object into a simple dict for metadata
            metadata_dict = extracted_data.model_dump()
            
            # IMPORTANT: Add the original filename back in
            metadata_dict["filename"] = doc.metadata.get("file_name", "Unknown")
            
            print(f"  Successfully extracted data from: {metadata_dict['filename']}")
            
            # Create a new Document, keeping the original text
            # but adding the *extracted* data as metadata
            new_doc = Document(
                text=doc.text,
                metadata=metadata_dict
            )
            normalized_documents.append(new_doc)
            
        except Exception as e:
            print(f"  Failed to extract data from {doc.metadata.get('file_name')}: {e}")

    if not normalized_documents:
        print("No documents were successfully normalized. Exiting.")
        return

    # --- 5. SET UP STORAGE (CHROMA DB) ---
    print("Setting up ChromaDB...")
    db = chromadb.PersistentClient(path="./storage/chroma_db")
    chroma_collection = db.get_or_create_collection("policy_docs")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # --- 6. CREATE THE INDEX (using the new docs) ---
    print(f"Indexing {len(normalized_documents)} normalized documents...")
    index = VectorStoreIndex.from_documents(
        normalized_documents, # Use the new list of docs with metadata
        storage_context=storage_context
    )
    
    print("✅ All documents successfully parsed, normalized, and indexed!")

if __name__ == "__main__":
    main()