# src/ingestion/extract_text.py

from pathlib import Path
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document

def extract_text_from_pdfs(pdf_path: Path) -> Document | None:
    """Loads a single PDF and returns a LlamaIndex Document object."""
    try:
        # Load all pages from the PDF
        reader = SimpleDirectoryReader(input_files=[pdf_path])
        documents = reader.load_data()
        
        # Combine pages into a single document for the subsequent classification input
        full_text = "\n\n".join([doc.text for doc in documents])
        
        # Return a single document representing the full file
        return Document(text=full_text, metadata={"filename": pdf_path.name})
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return None