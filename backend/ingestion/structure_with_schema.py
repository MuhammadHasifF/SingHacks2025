# src/ingestion/structure_with_schema.py

from typing import Dict, Any, List
from llama_index.llms.groq import Groq
from llama_index.core.schema import Document
from backend.ingestion.config.schema_definitions import ParameterExtractionSchema, EXTRACTION_PROMPT

def find_relevant_chunk(nodes: List[Document], item_name: str, item_type: str) -> str:
    """
    Searches classified nodes for the chunk that matches the taxonomy tag 
    and returns its text.
    """
    # Use the item name itself as the search criteria for a looser match
    target_name = item_name.replace("_", " ") 
    target_tag = f"{item_type}:{item_name}"
    
    # 1. Look for an exact match in the classified metadata (Ideal RAG)
    relevant_nodes = [
        node for node in nodes 
        if node.metadata.get("taxonomy_category") == target_tag
    ]
    
    if relevant_nodes:
        # Return the most relevant chunk text for extraction
        return relevant_nodes[0].text
    
    # 2. NEW FALLBACK: If no exact tag match, perform a simple text search 
    #    within the classified chunks as a mid-tier retrieval step.
    for node in nodes:
        if target_name.lower() in node.text.lower():
            print(f"   [NOTE] Found approximate match for '{target_name}' via text search.")
            return node.text
            
    
    print(f"   [WARN] No classified chunk found for {target_tag}. Using the full document text (first chunk) as a token-intensive fallback.")
    # 3. Final Fallback: Use the text of the first node (often the full document if the document was small)
    return nodes[0].text if nodes else ""

def extract_parameters_for_item(
    llm: Groq, 
    item_details: Dict[str, Any], 
    classified_nodes: List[Document],
    product_key: str
) -> Dict[str, Any] | None:
    """
    Finds the relevant text chunk using the taxonomy tag and calls Groq for parameter extraction.
    """
    item_name = item_details.get("condition") or item_details.get("benefit_name")
    item_type = item_details.get("condition_type") or "benefit"
        
    # Step 1: Targeted Retrieval (RAG)
    chunk_text = find_relevant_chunk(classified_nodes, item_name, item_type)
    
    if not chunk_text:
        return None # Cannot process if no text is available
        
    # Prepare prompt parameters
    expected_params = item_details.get("parameters", [])
    expected_params_list = ", ".join(expected_params) or "None (boolean existence check only)"
    
    print(f"   -> Extracting for {product_key}: {item_name} ({item_type})")

    try:
        # Step 2: Structured Extraction
        response = llm.structured_predict(
            output_cls=ParameterExtractionSchema,
            prompt=EXTRACTION_PROMPT,
            item_name=item_name,
            item_type=item_type,
            expected_parameters_list=expected_params_list,
            text=chunk_text, # LLM works on the retrieved chunk
        )
        
        extracted_data = response.dict()
        
        # Format the result to match the schema structure
        condition_exist_value = extracted_data.pop('condition_exist', False)
        
        return {
            "condition_exist": condition_exist_value,
            "original_text": extracted_data.get('original_text', ''),
            "parameters": extracted_data.get('parameters', {}),
            "confidence_score": extracted_data.get('confidence_score', 0.0),
        }
    
    except Exception as e:
        print(f"   [ERROR] Failed to extract parameters for {item_name} in {product_key}: {e}")
        return {
            "condition_exist": False,
            "original_text": "",
            "parameters": {},
            "error": str(e)
        }