# ingest.py
# This script loads PDFs using LlamaIndex and indexes them in ChromaDB.

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
# NEW, CORRECT line
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
import chromadb

# --- 1. LOAD AND PARSE DATA ---

# Point this to the folder containing your PDF files
pdf_folder_path = "./data/samples" 

print(f"Loading documents from {pdf_folder_path}...")

# This is the LlamaIndex way. It will automatically find
# pypdf, open all .pdf files, and extract the text.
reader = SimpleDirectoryReader(input_dir=pdf_folder_path)
documents = reader.load_data()

print(f"Successfully loaded {len(documents)} document(s).")
if documents:
    print(f"Example document source: {documents[0].metadata.get('file_name')}")

# --- 2. SET UP STORAGE AND INDEX ---

# Set up ChromaDB (using libraries from your requirements.txt)
db = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = db.get_or_create_collection("policy_docs")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 3. Create the index
# The 'documents' variable from SimpleDirectoryReader goes right in.
print("Indexing documents in ChromaDB...")
index = VectorStoreIndex.from_documents(
    documents, 
    storage_context=storage_context
)

print("✅ All documents successfully parsed and indexed!")