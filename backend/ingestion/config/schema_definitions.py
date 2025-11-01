# config/schema_definitions.py

from llama_index.core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from .taxonomy_loader import CLASSIFICATION_CATEGORIES

# ------------------------------------------------------------------
# 1. Batch Classification Schemas (For Token Saving)
# ------------------------------------------------------------------

class ClassificationSchema(BaseModel):
    """Schema for classifying a single document chunk."""
    chunk_id: int = Field(description="The unique integer ID of the chunk being classified, used for mapping.")
    category: str = Field(description=f"Select the single most appropriate category from this list: {CLASSIFICATION_CATEGORIES}")
    reasoning: str = Field(description="Brief explanation (1-2 sentences) of why this category was chosen.")

class BatchClassificationSchema(BaseModel):
    """Schema for classifying a batch of document chunks."""
    classifications: List[ClassificationSchema] = Field(
        description="A list containing the structured classification result for every chunk provided in the input text."
    )

CLASSIFICATION_PROMPT = PromptTemplate(
    template="""
    You are a professional document classifier. Your task is to classify ALL the provided text chunks 
    into the **SINGLE, MOST RELEVANT** taxonomy category from the available list.
    
    CRITICAL RULE 1: For every 'CHUNK ID' in the input, you MUST output **only ONE** 'ClassificationSchema' object in the JSON list. 
    CRITICAL RULE 2: The 'category' field MUST be selected **exactly** from the provided list below. Do NOT modify the category name.

    If a chunk contains information about one of the categories, select that category, even if the phrasing differs slightly.

    Available Categories:
    {categories}

    --- CHUNKS TO CLASSIFY ---
    {chunks_text}
    """
)

# ------------------------------------------------------------------
# 2. Parameter Extraction Schema (For Final Structuring)
# ------------------------------------------------------------------

class ParameterExtractionSchema(BaseModel):
    """Schema for extracting the concrete parameters for a specific condition/benefit."""
    condition_exist: bool = Field(description="Set to true if the text clearly describes the condition/benefit; false otherwise.")
    original_text: str = Field(description="The exact sentence(s) or paragraph from the text that describes the condition/benefit. Use empty string if not found.")
    parameters: Dict[str, Any] = Field(description="A dictionary of all concrete values extracted for the expected parameters (e.g., {'limit': 'USD 50,000'}). Keys must match the expected parameter names. If a parameter is not found, use the value 'N/A'.")
    confidence_score: float = Field(description="A confidence score between 0.0 and 1.0 on the extraction accuracy.")

EXTRACTION_PROMPT = PromptTemplate(
    template="""
    You are an expert financial and insurance data extraction assistant.
    Your task is to extract concrete values from the text provided, strictly adhering to the Pydantic Schema.

    CONTEXT: You are extracting details for the specific item: '{item_name}' 
    which is a '{item_type}'.
    
    EXPECTED PARAMETERS: {expected_parameters_list}

    EXTRACTION RULES:
    1. 'condition_exist' must be true if the text is relevant.
    2. 'original_text' must contain the exact source text retrieved by the classifier.
    3. The keys in the 'parameters' object MUST match the 'EXPECTED PARAMETERS' list. 
       If a parameter is not explicitly found, use the value 'N/A'.

    TEXT CHUNK TO ANALYZE:
    {text}
    """
)