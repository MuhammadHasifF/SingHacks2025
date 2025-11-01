# MSIG Travel Assistant - Conversational Insurance AI - https://msigtravelassistant.streamlit.app/

**A breakthrough conversational AI that transforms travel insurance from tedious forms into an engaging, intelligent dialogue.** Built for SingHacks 2025 as part of the Ancileo × MSIG collaboration.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Architecture](#architecture)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The MSIG Travel Assistant is an AI-powered conversational agent that helps users:
- **Compare insurance plans** (TravelEasy, TravelEasy Pre-Ex, Scootsurance)
- **Understand policy terms** and coverage details
- **Check eligibility** for pre-existing conditions
- **Get personalized recommendations** based on travel itinerary
- **Extract information** from travel documents (itineraries, tickets, policies)
- **Generate dynamic quotes** with real-time pricing

The system uses **Groq's ultra-low-latency LLM** (Llama 3.3 70B) combined with **LangChain** for conversation management, providing natural, context-aware responses that adapt to user tone and emotional state.

---

## Features

### Intelligent Conversation
- **Psychological adaptation**: Detects user mood (unsure, urgent, confused, ready to buy) and adjusts tone accordingly
- **Multi-turn dialogue**: Maintains conversation context with session memory
- **Intent detection**: Automatically routes questions to appropriate handlers (comparison, explanation, eligibility, scenarios)

### Policy Intelligence
- **Plan comparison**: Side-by-side comparison of MSIG travel insurance products
- **Coverage lookup**: Detailed information about medical, cancellation, death/dismemberment coverage
- **Eligibility checking**: Pre-existing condition coverage verification
- **Scenario analysis**: Answers "what if" questions (e.g., "What if I break my leg skiing?")

### Document Processing
- **Itinerary extraction**: Parses travel itineraries to extract dates, destinations, costs, and trip details
- **Ticket parsing**: Extracts flight information, booking details, and passenger data
- **Policy summarization**: Analyzes insurance policy documents
- **LLM-powered extraction**: Uses Groq LLM for intelligent document understanding

### Quote Generation
- **Dynamic pricing**: Calculates premiums based on trip duration
- **Plan recommendations**: Suggests the best plan based on trip cost and coverage needs
- **Real-time quotes**: Generates instant quotes with coverage details and policy links

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | Streamlit (Python web app) |
| **Backend API** | FastAPI (REST API) |
| **LLM** | Groq (Llama 3.3 70B Versatile) |
| **AI Framework** | LangChain 1.x |
| **Document Processing** | PyMuPDF (fitz), LlamaIndex |
| **Vector DB** | ChromaDB (optional, for future RAG) |
| **Embeddings** | HuggingFace (BAAI/bge-small-en-v1.5) |
| **Session Storage** | Local JSON files |
| **Deployment** | Railway, Docker |

### Python Version
- **Python 3.13.7** (compatible with 3.10+)

---

## Project Structure

```
SingHacks2025/
│
├── README.md                       # This file
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
├── .env.example                    # Environment variables template
│
├── app/                            # Streamlit Frontend
│   ├── main.py                     # Main Streamlit app entry point
│   │                               # - Chat interface with MSIG branding
│   │                               # - Session management
│   │                               # - Message persistence
│   │
│   ├── components/
│   │   └── upload_panel.py         # Sidebar upload component
│   │                               # - File upload (itinerary/ticket/policy)
│   │                               # - Document extraction UI
│   │                               # - Quote generation display
│   │
│   ├── styles/
│   │   └── (empty - styles in main.py)
│   │
│   ├── utils/
│   │   └── (empty - utilities in main.py)
│   │
│   └── msig_theme.css              # Additional MSIG styling (if needed)
│
├── backend/                        # Core Backend Logic
│   ├── api.py                      # FastAPI application
│   │                               # - POST /chat: Chat endpoint
│   │                               # - POST /upload: File upload
│   │                               # - POST /upload_extract: Extract document data
│   │                               # - POST /generate_quotes: Quote generation
│   │                               # - GET /policy_pdf/{filename}: Serve PDFs
│   │                               # - GET /health: Health check
│   │
│   ├── config.py                   # Configuration management
│   │                               # - Environment variable loading
│   │                               # - GROQ_API_KEY validation
│   │                               # - App settings
│   │
│   ├── groq/                       # Groq LLM Integration
│   │   ├── client.py               # Groq SDK wrapper
│   │   │                           # - Direct Groq API client
│   │   │                           # - Chat completion interface
│   │   │
│   │   └── groq_llm.py             # LangChain Groq integration
│   │                               # - ChatGroq wrapper
│   │                               # - Model initialization
│   │
│   ├── chains/                     # LangChain Processing Chains
│   │   ├── conversational_agent.py # Main conversational agent
│   │   │                           # - LLM chain creation
│   │   │                           # - Session memory management
│   │   │                           # - Tone adaptation logic
│   │   │                           # - Response generation
│   │   │
│   │   ├── question_handler.py     # Question routing
│   │   │                           # - Intent classification
│   │   │                           # - Routes to comparison/explanation/eligibility
│   │   │
│   │   ├── policy_comparator.py    # Policy comparison logic
│   │   │                           # - Loads combined taxonomy
│   │   │                           # - Compares two policies
│   │   │                           # - Explains sections
│   │   │                           # - Checks eligibility
│   │   │                           # - Scenario coverage lookup
│   │   │
│   │   ├── intent.py               # Intent detection
│   │   │                           # - Keyword-based intent classification
│   │   │                           # - Returns: comparison/explanation/eligibility/scenario/general
│   │   │
│   │   ├── response_formatter.py   # Response formatting
│   │   │                           # - Standardizes API responses
│   │   │                           # - Adds metadata and citations
│   │   │
│   │   └── citation_helper.py      # Citation management
│   │                               # - Adds PDF links to responses
│   │                               # - Formats markdown citations
│   │
│   ├── ingestion/                  # Document Processing Pipeline
│   │   ├── pdf_loader.py           # PDF text extraction
│   │   │                           # - Uses PyMuPDF (fitz)
│   │   │                           # - Extracts plain text from PDFs
│   │   │
│   │   ├── parse_pdf.py            # Mock PDF parser (legacy)
│   │   │                           # - Placeholder for OCR/parsing
│   │   │
│   │   ├── llama_structurer.py     # LLM-based document structuring
│   │   │                           # - Initializes Groq LLM + embeddings
│   │   │                           # - Structures extracted text into JSON
│   │   │                           # - Uses HuggingFace embeddings
│   │   │
│   │   ├── taxonomy_mapper.py      # Taxonomy schema builder
│   │   │                           # - Loads taxonomy JSON schema
│   │   │                           # - Builds extraction prompts
│   │   │
│   │   ├── process_all_policies.py # Batch policy processor
│   │   │                           # - Processes all PDFs in Policy_Wordings
│   │   │                           # - Chunks large documents
│   │   │                           # - Structures each chunk
│   │   │
│   │   └── combine_to_taxonomy.py  # Taxonomy combiner
│   │                               # - Combines individual policy JSONs
│   │                               # - Maps to unified taxonomy structure
│   │                               # - Generates combined_taxonomy_policies.json
│   │
│   ├── index/                      # Vector Indexing (for future RAG)
│   │   └── (empty - ChromaDB integration pending)
│   │
│   ├── storage/                    # Data Storage
│   │   └── (empty - using JSON files directly)
│   │
│   └── utils/                      # Utility Functions
│       ├── policy_extractor.py     # Document information extraction
│       │                           # - Extract itinerary info (dates, destination, cost)
│       │                           # - Extract ticket info (flight, passenger)
│       │                           # - Extract policy summary
│       │                           # - Get recommended plan
│       │                           # - Calculate dynamic pricing
│       │
│       └── taxonomy_reader.py      # Taxonomy data loader
│                                   # - Loads policy coverage from JSON
│                                   # - Fallback to known coverage mappings
│                                   # - Returns medical/cancellation/death coverage
│
├── data/                           # Data Directory
│   ├── Policy_Wordings/            # Original policy PDFs
│   │   ├── TravelEasy Policy QTD032212.pdf
│   │   ├── TravelEasy Pre-Ex Policy QTD032212-PX.pdf
│   │   └── Scootsurance QSR022206_updated.pdf
│   │
│   ├── taxonomy/                   # Taxonomy schema
│   │   └── Taxonomy_Hackathon.json # Insurance product taxonomy structure
│   │
│   ├── samples/                    # Sample processed JSONs
│   │   ├── TravelEasy Policy QTD032212.json
│   │   ├── TravelEasy Pre-Ex Policy QTD032212-PX.json
│   │   └── Scootsurance QSR022206.json
│   │
│   ├── processed/                  # Processed/combined data
│   │   └── combined_taxonomy_policies.json  # Unified policy taxonomy
│   │
│   ├── uploads/                    # User-uploaded documents (gitignored)
│   │   └── (user files stored here)
│   │
│   └── chroma_db/                  # ChromaDB vector store (gitignored)
│       └── (vector embeddings if using RAG)
│
├── tests/                          # Test Suite
│   ├── test_cli_chat.py            # CLI chat interface tester
│   ├── test_conversation.py        # Conversation flow tests
│   └── test_policy_functions.py    # Policy comparison/explanation tests
│
├── deployment/                     # Deployment Configs
│   └── (empty - deployment configs removed)
│
├── storage/                        # Runtime Storage (gitignored)
│   └── history/                    # User session history
│       └── (JSON session files)
│
└── .sessions/                      # Streamlit Sessions (gitignored)
    └── (user session JSON files)
```

### Key File Descriptions

#### Frontend (`app/`)
- **`main.py`**: Entry point for Streamlit app. Handles chat UI, session management, message persistence, and MSIG-themed styling.

#### Backend Core (`backend/`)
- **`api.py`**: FastAPI server with chat, upload, extraction, and quote generation endpoints.
- **`config.py`**: Centralized configuration loading from environment variables.

#### AI & LLM (`backend/chains/`, `backend/groq/`)
- **`conversational_agent.py`**: Creates LangChain agent with Groq LLM, manages conversation memory, implements tone adaptation.
- **`question_handler.py`**: Routes user questions to appropriate policy logic handlers.
- **`policy_comparator.py`**: Core policy comparison, explanation, and eligibility checking logic.

#### Document Processing (`backend/ingestion/`, `backend/utils/`)
- **`pdf_loader.py`**: Extracts text from PDF files using PyMuPDF.
- **`policy_extractor.py`**: Uses Groq LLM to extract structured data from travel documents.
- **`combine_to_taxonomy.py`**: Combines individual policy JSONs into unified taxonomy structure.

#### Data (`data/`)
- **`Policy_Wordings/`**: Original MSIG policy PDF documents.
- **`processed/combined_taxonomy_policies.json`**: Unified JSON structure containing all policy data.
- **`taxonomy/Taxonomy_Hackathon.json`**: Schema definition for insurance product taxonomy.

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+** (tested with Python 3.13.7)
- **pip** (Python package manager)
- **Git** (for cloning the repository)
- **Groq API Key** ([Get one here](https://console.groq.com/))

### Optional (for deployment):
- **Docker** (for containerized deployment)
- **Railway account** (for cloud deployment)

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/SingHacks2025.git
cd SingHacks2025
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy example file (if available)
cp .env.example .env
```

Or create `.env` manually with the following content:

```env
# Required: Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# Optional: App Configuration
APP_ENV=local
LOG_LEVEL=INFO
CHROMA_PERSIST_DIR=./data/chroma_db

# Optional: Tavily API (for web search, if needed)
TAVILY_API_KEY=your_tavily_key_here
```

**Important**: Replace `your_groq_api_key_here` with your actual Groq API key from [Groq Console](https://console.groq.com/).

### 5. Verify Setup

Test that the backend can start:

```bash
# Test backend health
python -c "from backend.config import GROQ_API_KEY; print('Config loaded' if GROQ_API_KEY else 'Missing API key')"
```

---

## Usage

### Running Locally (Development)

#### Option 1: Separate Terminals (Recommended for Development)

**Terminal 1 - Start Backend API:**
```bash
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Terminal 2 - Start Frontend:**
```bash
streamlit run app/main.py
```

You should see:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Open your browser to **http://localhost:8501** to use the app.

#### Option 2: Docker (Production-like)

```bash
# Build Docker image
docker build -t msig-assistant .

# Run container
docker run -p 8501:8501 -p 8000:8000 --env-file .env msig-assistant
```

### Using the Application

1. **Chat Interface**: Type questions in the chat box:
   - "Compare TravelEasy and Scootsurance"
   - "What does trip cancellation cover?"
   - "Am I covered for pre-existing conditions?"
   - "What if I break my leg skiing in Japan?"

2. **Document Upload**: Use the sidebar to upload:
   - **Itinerary**: Travel booking documents
   - **Ticket**: Flight tickets
   - **Policy**: Insurance policy documents

3. **Quote Generation**: After uploading documents, click "Generate Quotes" to see:
   - Plan comparisons
   - Dynamic pricing based on trip duration
   - Recommended plan based on your trip

### Testing the Backend API

```bash
# Health check
curl http://localhost:8000/health

# Chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Compare medical coverage", "session_id": "test123"}'
```

---

## API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "ok": true,
  "groq_key_set": true
}
```

### `POST /chat`
Main chat endpoint for conversational queries.

**Request:**
```json
{
  "question": "Compare TravelEasy and Scootsurance",
  "session_id": "user_123"
}
```

**Response:**
```json
{
  "text": "TravelEasy offers...",
  "intent": "comparison",
  "session_id": "user_123",
  "citations": ["MSIG TravelEasy / Pre-Ex / Scootsurance Official Policy Wordings (2025)"],
  "meta": {"model": "llama-3.3-70b-versatile"}
}
```

### `POST /upload`
Upload a file to the server.

**Request:** `multipart/form-data` with `file` field

**Response:**
```json
{
  "ok": true,
  "filename": "itinerary.pdf",
  "path": "data/uploads/itinerary.pdf"
}
```

### `POST /upload_extract`
Upload and extract information from a document.

**Request:** `multipart/form-data` with:
- `file`: PDF file
- `doc_type`: "itinerary" | "ticket" | "policy"

**Response:**
```json
{
  "ok": true,
  "filename": "itinerary.pdf",
  "doc_type": "itinerary",
  "data": {
    "traveler_name": "John Doe",
    "destination": "Tokyo, Japan",
    "dates": "2025-03-15 to 2025-03-22",
    "trip_cost": 2500,
    "duration": 7
  }
}
```

### `POST /generate_quotes`
Generate insurance quotes based on trip data.

**Request:**
```json
{
  "trip_data": {
    "trip_cost": 2500,
    "duration": 7,
    "destination": "Japan"
  }
}
```

**Response:**
```json
{
  "ok": true,
  "trip": {...},
  "quotes": [
    {
      "plan": "TravelEasy Policy QTD032212",
      "medical": "$100,000",
      "cancellation": "$5,000",
      "price": "$42.50",
      "link": "http://127.0.0.1:8000/policy_pdf/..."
    }
  ],
  "recommended_plan": "TravelEasy Policy QTD032212"
}
```

### `GET /policy_pdf/{filename}`
Serve policy PDF files.

**Example:** `GET /policy_pdf/TravelEasy%20Policy%20QTD032212.pdf`

---

## Architecture

### High-Level Flow

```
User Query
    ↓
Streamlit UI (app/main.py)
    ↓
FastAPI Backend (backend/api.py)
    ↓
Intent Detection (backend/chains/intent.py)
    ↓
Question Handler (backend/chains/question_handler.py)
    ↓
Policy Comparator / LLM Processing
    ↓
Groq LLM (backend/groq/)
    ↓
Response Formatter (backend/chains/response_formatter.py)
    ↓
Frontend Display
```

### Component Interaction

1. **User Input** → Streamlit chat interface
2. **Session Management** → JSON files in `.sessions/`
3. **API Request** → FastAPI `/chat` endpoint
4. **Intent Detection** → Keyword-based classification
5. **Question Routing** → Policy logic or LLM processing
6. **LLM Generation** → Groq Llama 3.3 70B
7. **Citation Addition** → PDF links appended
8. **Response Return** → Formatted JSON to frontend

### Document Processing Flow

```
PDF Upload
    ↓
PDF Text Extraction (pdf_loader.py)
    ↓
LLM Extraction (policy_extractor.py)
    ↓
Structured JSON Output
    ↓
Quote Generation (generate_quotes endpoint)
```

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Individual Test Files

```bash
# Test conversation flow
pytest tests/test_conversation.py -v

# Test policy functions
pytest tests/test_policy_functions.py -v

# Test CLI chat interface
python tests/test_cli_chat.py
```

### Manual Testing

1. **Backend API:**
   ```bash
   # Start backend
   uvicorn backend.api:app --reload
   
   # Test in another terminal
   curl http://localhost:8000/health
   ```

2. **Frontend:**
   ```bash
   streamlit run app/main.py
   # Open http://localhost:8501 and interact with the UI
   ```

---

## Deployment

### Railway Deployment

1. **Create Railway Account**: [railway.app](https://railway.app)

2. **Link Repository**: Connect your GitHub repo to Railway

3. **Set Environment Variables**:
   - `GROQ_API_KEY`: Your Groq API key
   - `APP_ENV`: `production`

4. **Deploy**: Railway will auto-detect and deploy

### Docker Deployment

```bash
# Build image
docker build -t msig-assistant .

# Run with environment file
docker run -p 8501:8501 -p 8000:8000 --env-file .env msig-assistant
```

### Manual Server Deployment

1. **SSH into server**
2. **Clone repository**
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Set environment variables**
5. **Run with process manager** (PM2, supervisor, etc.):
   ```bash
   # Backend
   uvicorn backend.api:app --host 0.0.0.0 --port 8000
   
   # Frontend
   streamlit run app/main.py --server.port 8501
   ```

---

## Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GROQ_API_KEY` | Yes | Groq API key for LLM access | - |
| `APP_ENV` | No | Environment (local/production) | `local` |
| `LOG_LEVEL` | No | Logging level | `INFO` |
| `CHROMA_PERSIST_DIR` | No | ChromaDB storage path | `./data/chroma_db` |
| `TAVILY_API_KEY` | No | Tavily API key (optional) | - |

---

## Troubleshooting

### Common Issues

1. **"GROQ_API_KEY not set" Error**
   - Ensure `.env` file exists in root directory
   - Check that `GROQ_API_KEY` is set correctly
   - Restart the application after adding the key

2. **Port Already in Use**
   ```bash
   # Change ports in commands:
   uvicorn backend.api:app --port 8001
   streamlit run app/main.py --server.port 8502
   ```

3. **Import Errors**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt` again
   - Check Python version: `python --version` (should be 3.10+)

4. **PDF Extraction Fails**
   - Verify PDF file is not corrupted
   - Check file path is correct
   - Ensure PyMuPDF is installed: `pip install pymupdf`

5. **Session Not Persisting**
   - Check `.sessions/` directory exists and is writable
   - Verify file permissions on the directory

---

## Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Code Style
- Follow PEP 8 Python style guide
- Use type hints where possible
- Add docstrings to functions and classes
- Keep functions focused and modular

---

## License

This project is part of SingHacks 2025 and is built for the Ancileo × MSIG collaboration.

---

## Acknowledgments

- **Groq** for ultra-low-latency LLM inference
- **LangChain** for AI agent framework
- **Streamlit** for rapid UI development
- **FastAPI** for modern Python web framework
- **MSIG** for policy documents and domain expertise

---

## Contact & Support

For questions, issues, or contributions:
- **GitHub Issues**: [Open an issue](https://github.com/your-username/SingHacks2025/issues)
- **Email**: [Your email]

---

## Future Enhancements

- [ ] Vector database (ChromaDB) integration for RAG
- [ ] Voice input/output support
- [ ] Multi-language support
- [ ] Real-time policy updates
- [ ] Advanced analytics dashboard
- [ ] Mobile app version

---

**Built for SingHacks 2025**

