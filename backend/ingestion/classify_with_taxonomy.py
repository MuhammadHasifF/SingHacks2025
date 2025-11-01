# src/ingestion/classify_with_taxonomy.py

from llama_index.llms.groq import Groq
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document
from backend.ingestion.config.schema_definitions import BatchClassificationSchema, CLASSIFICATION_PROMPT, CLASSIFICATION_CATEGORIES
from typing import List
import time # Import time for retries

# Define the batch size (controls the number of chunks per API call)
# INCREASED BATCH SIZE to reduce API calls and save tokens
BATCH_SIZE = 4
# Smallest, fastest, and cheapest model for bulk classification
CLASSIFICATION_MODEL = "llama-3.1-8b-instant" 

def create_batches(nodes: List[Document]) -> List[List[Document]]:
    """Groups the nodes into batches of BATCH_SIZE."""
    batches = []
    for i in range(0, len(nodes), BATCH_SIZE):
        batches.append(nodes[i:i + BATCH_SIZE])
    return batches

def format_chunks_for_llm(batch: List[Document]) -> str:
    """Formats a batch of chunks into a single string for the prompt."""
    formatted_text = []
    for i, node in enumerate(batch):
        chunk_id = hash(node.text) % 100000 
        node.metadata["temp_chunk_id"] = chunk_id # Store the ID for mapping later
        
        formatted_text.append(f"--- CHUNK ID {chunk_id} ---\n{node.text}\n")
        
    return "\n".join(formatted_text)

def classify_document_chunks(document: Document, llm: Groq) -> List[Document]:
    """
    Splits the document, batches the chunks, and classifies them using 
    one API call per batch.
    """
    # Re-initialize LLM specifically for classification
    classification_llm = Groq(model=CLASSIFICATION_MODEL, temperature=0, api_key=llm.api_key)
    
    print(f"🔬 Classifying chunks for: {document.metadata.get('filename', 'Unknown')} using {CLASSIFICATION_MODEL}")
    
    # 1. Chunk the document
    # Increased chunk overlap/size slightly to reduce total chunks
    parser = SentenceSplitter(chunk_size=512, chunk_overlap=100)
    nodes = parser.get_nodes_from_documents([document])
    
    # 2. Batch the chunks
    batches = create_batches(nodes)
    category_list_str = ", ".join(CLASSIFICATION_CATEGORIES)
    all_classified_nodes = []
    
    print(f"   Splitting into {len(nodes)} chunks and {len(batches)} batches (Batch Size: {BATCH_SIZE})...")

    # 3. Process batches
    for i, batch in enumerate(batches):
        print(f"   -> Processing Batch {i+1}/{len(batches)}...")
        
        # Format input for the LLM
        chunks_text = format_chunks_for_llm(batch)
        
        # Implement a retry loop for rate limit errors
        max_retries = 3
        delay = 5 # seconds
        for attempt in range(max_retries):
            try:
                # LLM Call for Structured Batch Classification (Single API Call)
                response = classification_llm.structured_predict(
                    output_cls=BatchClassificationSchema,
                    prompt=CLASSIFICATION_PROMPT,
                    categories=category_list_str,
                    chunks_text=chunks_text,
                )
                
                # Success: Map results back and break retry loop
                results_map = {c.chunk_id: c.category for c in response.classifications}
                
                for node in batch:
                    chunk_id = node.metadata.pop("temp_chunk_id")
                    if category := results_map.get(chunk_id):
                        node.metadata["taxonomy_category"] = category
                    
                    all_classified_nodes.append(node)
                
                break # Exit the retry loop on success
            
            except Exception as e:
                error_message = str(e)
                if "Rate limit reached" in error_message or "429 Too Many Requests" in error_message:
                    if attempt < max_retries - 1:
                        print(f"   [RATE LIMIT] Attempt {attempt+1} failed. Retrying in {delay} seconds...")
                        time.sleep(delay)
                        delay *= 2 # Exponential backoff
                    else:
                        print(f"   [ERROR] Failed to classify Batch {i+1} after {max_retries} attempts: {e}. Retaining original chunks.")
                        all_classified_nodes.extend(batch)
                        break
                else:
                    # Handle other non-rate-limit errors (e.g., bad JSON)
                    print(f"   [ERROR] Failed to classify Batch {i+1}: {e}. Retaining original chunks.")
                    all_classified_nodes.extend(batch)
                    break
            
    print(f"✅ Classification complete. {len(all_classified_nodes)} chunks processed.")
    return all_classified_nodes