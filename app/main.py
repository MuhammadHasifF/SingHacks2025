# app/main.py
import streamlit as st
import chromadb
from dotenv import load_dotenv

# LlamaIndex imports
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.core import Settings
from llama_index.core.vector_stores import (
    MetadataFilter, 
    MetadataFilters, 
    FilterOperator
)

# Load API keys from .env
load_dotenv()

# --- 1. CONFIGURE MODELS (LLM and Embedding) ---
# We configure this globally for all Streamlit sessions
@st.cache_resource
def configure_models():
    print("Configuring models...")
    Settings.llm = Groq(model="llama3-8b-8192")
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )

# --- 2. LOAD THE EXISTING INDEX FROM CHROMA ---
# We cache this to prevent reloading on every interaction
@st.cache_resource
def load_index():
    print("Loading index from ChromaDB...")
    db = chromadb.PersistentClient(path="./storage/chroma_db")
    chroma_collection = db.get_collection(name="policy_docs")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    
    # Re-load the index from the vector store
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
    )
    print("✅ Index loaded successfully.")
    return index

# --- 3. CONFIGURE STREAMLIT PAGE ---
st.set_page_config(page_title="Policy Q&A Bot", layout="centered")
st.title("📄 Policy Q&A Bot")
st.markdown("Ask me anything about your policy documents!")

# --- 4. INITIALIZE MODELS AND INDEX ---
configure_models()
index = load_index()

# --- 5. SETUP SIDEBAR FOR METADATA FILTERING ---
st.sidebar.title("Search Filters")
policy_filter = st.sidebar.text_input(
    "Filter by Policy Number:",
    placeholder="e.g., policy_sample"
)
st.sidebar.markdown(
    "Enter a policy number to search *only* within that document."
)

# --- 6. INITIALIZE CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 7. HANDLE USER INPUT AND QUERY ---
if prompt := st.chat_input("Your question"):
    # Add user message to session state and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Create the query engine with the filter ---
    # This is the most important part!
    filters = None
    if policy_filter:
        st.info(f"Searching with filter: `policy_number == \"{policy_filter}\"`")
        filters = MetadataFilters(
            filters=[
                MetadataFilter(
                    key="policy_number", 
                    operator=FilterOperator.EQ, 
                    value=policy_filter
                )
            ]
        )

    # Create a query engine *for this specific query*
    query_engine = index.as_query_engine(
        filters=filters,
        streaming=True  # Enable streaming for Groq
    )

    # --- Get and display the assistant's response ---
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Get the streaming response
            streaming_response = query_engine.query(prompt)
            
            # Use write_stream to display the streaming text
            response_content = st.write_stream(streaming_response.response_gen)
    
    # Add the full response to session state
    st.session_state.messages.append(
        {"role": "assistant", "content": response_content}
    )