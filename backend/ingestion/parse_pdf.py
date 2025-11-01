# ingest.py
# This script loads PDFs using LlamaIndex and indexes them.

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import json
import chromadb

# --- 1. CONFIGURE LLM AND EMBEDDING ---
llm = Groq(model="llama-3.3-70b-versatile", temperature=0.3)
embedding_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# --- 2. PARSE PDF FILES ---
pdf_folder_path = "./data/samples"
print(f"Loading documents from {pdf_folder_path}...")

# Use SimpleDirectoryReader to parse PDFs
documents = SimpleDirectoryReader(pdf_folder_path).load_data()

# --- 3. INDEX DOCUMENTS ---
print("Indexing documents...")
vector_store = VectorStoreIndex.from_documents(documents, llm=llm, embed_model=embedding_model)

# --- 4. SAVE ALL DOCUMENTS AS A SINGLE JSON FILE ---
# Specify the output file for the combined JSON
combined_json_file_path = "./data/processed/non_normalized_parsed_pdf.json"

print(f"Saving all extracted documents to {combined_json_file_path}...")

# Combine all documents into a single JSON structure
combined_json_data = []
for doc in documents:
    combined_json_data.append({
        "content": doc.text,
        "metadata": doc.metadata,
    })

# Save the combined JSON data to a single file
with open(combined_json_file_path, "w", encoding="utf-8") as combined_json_file:
    json.dump(combined_json_data, combined_json_file, ensure_ascii=False, indent=4)

print(f"✅ All documents saved to {combined_json_file_path}")

# --- 5. SAVE TO CHROMADB ---
# print("Saving documents to ChromaDB...")

# # Initialize ChromaDB client
# chroma_client = chromadb.PersistentClient(path="./storage/chroma_db")

# # Create or get the collection
# collection_name = "policy_docs"
# if not chroma_client.has_collection(collection_name):
#     chroma_collection = chroma_client.create_collection(name=collection_name)
# else:
#     chroma_collection = chroma_client.get_collection(name=collection_name)

# # Add documents to the collection
# for doc in documents:
#     chroma_collection.add(
#         documents=[doc.text],
#         metadatas=[doc.metadata],
#         ids=[doc.metadata.get("file_name", "unknown")]
#     )

# print("✅ Documents successfully saved to ChromaDB.")

# --- 6. PRINT JSON FORMAT IN CONSOLE ---
print("\nDisplaying extracted documents in JSON format:")
for i, doc in enumerate(documents):
    json_data = {
        "content": doc.text,
        "metadata": doc.metadata,
    }
    print(f"Document {i + 1}:")
    print(json.dumps(json_data, ensure_ascii=False, indent=4))
    print("\n---\n")