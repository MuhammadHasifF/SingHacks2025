# query.py
import chromadb
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.vector_stores import (
    MetadataFilter, 
    MetadataFilters, 
    FilterOperator
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.core import Settings
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

# --- 1. CONFIGURE MODELS (LLM and Embedding) ---
Settings.llm = Groq(model="llama3-8b-8192")
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

# --- 2. LOAD THE EXISTING INDEX FROM CHROMA ---
print("Loading index from ChromaDB...")
db = chromadb.PersistentClient(path="./storage/chroma_db")
chroma_collection = db.get_collection(name="policy_docs")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
print("✅ Index loaded successfully.")

# --- 3. RUN A FILTERED QUERY ---

# Define a filter based on your new taxonomy
# Let's find a specific policy document
doc_filter = MetadataFilters(
    filters=[
        MetadataFilter(
            key="policy_number", 
            operator=FilterOperator.EQ, 
            value="policy_sample" # Change to a real policy number
        ),
        # You could also filter by document type:
        # MetadataFilter(
        #    key="document_type", 
        #    operator=FilterOperator.EQ, 
        #    value="Policy Declaration"
        # )
    ]
)

# Create a retriever that USES the filter
retriever = index.as_retriever(
    filters=doc_filter
)

# Now, create a query engine from that specific retriever
query_engine = index.as_query_engine(
    retriever=retriever
)

# The query is now much simpler and runs *only* on the filtered documents
query_text = "What is the policy holder's name?"

print(f"\n--- Querying with filter: {doc_filter.to_dict()} ---")
response = query_engine.query(query_text)

print("\n--- Query Response ---")
print(response)

print("\n--- Source Nodes ---")
for node in response.source_nodes:
    print(f"Source: {node.metadata.get('filename')}")
    print(f"Policy: {node.metadata.get('policy_number')}")
    print(f"Score: {node.score}")
    print("-" * 20)