# test_db.py
import chromadb
from backend.ingestion.ingest_docs import ingest_documents

# Trigger the ingestion process before connecting to ChromaDB
print("Starting the ingestion process...")
ingest_documents()
print("Ingestion process completed.")

print("Connecting to existing ChromaDB...")
client = chromadb.PersistentClient(path="./storage/chroma_db")

# Get the collection you created in ingest.py
collection = client.get_collection(name="policy_docs")

# Get the total number of items
count = collection.count()
print(f"Database contains {count} documents.")

if count > 0:
    print("\nPeeking at 5 items from the database:")
    data = collection.peek(limit=5)
    print(data)