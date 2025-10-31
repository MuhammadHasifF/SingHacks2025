# backend/ingestion/metadata_schema.py
from pydantic import BaseModel, Field
from typing import List, Optional

class PolicyDetails(BaseModel):
    """The structured taxonomy for an insurance policy document."""
    
    policy_number: str = Field(
        ..., description="The unique identifier for the policy, e.g., 'ABC-12345'"
    )
    policy_holder: str = Field(
        ..., description="The full name of the primary person insured"
    )
    document_type: str = Field(
        ..., description="The type of document, e.g., 'Policy Declaration', 'Certificate of Insurance', 'Renewal Notice'"
    )
    coverage_types: List[str] = Field(
        default=[], description="A list of coverages, e.g., ['Collision', 'Liability']"
    )
    # Add any other fields you want to extract