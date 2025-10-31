# ⚡ SingHacks 2025: Asia's Agentic AI Hackathon ⚡

**Welcome to SingHacks 2025!** This isn't just another hackathon; it’s your weekend playground to experiment, push boundaries, and create something unforgettable.

We are Asia's first **agentic AI hackathon** dedicated to fintech innovation. Unlock new skills, expand your network, and build dope things with the potential to win exciting prizes.

---

## 📅 Hackathon Overview

| Detail | Information |
| :--- | :--- |
| **Dates** | **October 31 – November 2, 2025** (Friday Evening – Sunday Evening) |
| **Theme** | Agentic AI for Fintech (RegTech, Finance, Insurance) |
| **Discord** | 🔗 [Join the SingHacks Discord Server]([Discord Invite Link Here]) |
| **Contact** | 🆘 [Contact us]([Contact Form/Email Link Here]) |

---

### 📍 Venues & Schedule

The event is split across two locations:

| Date | Time | Event | Venue | Address |
| :--- | :--- | :--- | :--- | :--- |
| **Fri, Oct 31** | 6:00 PM – 9:00 PM | **Opening Ceremony** | **VISA** (Network Partner) | 71 Robinson Road, #08-01, Singapore 068895 |
| **Sat, Nov 1** | 9:00 AM – 9:00 PM | **Hackathon Day 1** | **Catapult** (Network Partner) | 1 Rochester Park, #02-01, Singapore 139212 |
| **Sun, Nov 2** | 9:00 AM – 6:00 PM | **Hackathon Day 2 & Closing** | **Catapult** (Network Partner) | 1 Rochester Park, #02-01, Singapore 139212 |

> **Note:** After the Opening Ceremony at VISA on Friday, all participants must head directly to **Catapult** for the remainder of the weekend (Saturday & Sunday).

---

## 🛠️ Challenge Tracks

This year's hackathon focuses on building **agentic AI systems** within key financial sectors. Choose the track that excites you most and start brainstorming!

### 1) RegTech Intelligence
Build agentic AI systems that surface compliance risks, flag transactions, and streamline onboarding.

### 2) Conversational Insurance (This Repo)
Build agentic AI systems that transform travel insurance into a seamless conversational journey.

---

## 🧰 Project: Ancileo × MSIG — Conversational Insurance (“Insurance Jazzbot”)

**Goal:** Create a breakthrough conversational AI that turns insurance from tedious forms into an engaging, intelligent dialogue. Real-time, personalized, and delightful.

**Tech Stack**
- **Frontend:** Streamlit (chat UI, uploads, policy comparison, payment simulation)
- **Backend:** FastAPI (webhooks, ingestion), LangChain (agents, tools), LlamaIndex (doc → index pipeline)
- **Inference:** Groq LPU™ (ultra-low-latency LLM)
- **Vector DB:** Chroma (local-first)
- **Search/Tools:** Tavily (optional), custom premium calculator
- **Deploy:** Railway (Dockerized)

---

## 📁 Project Structure

```plaintext
SingHacks2025/
│
├── README.md                  # Ancileo × MSIG overview + setup guide
├── requirements.txt
├── .env.example
├── .gitignore
│
├── app/                       # 🪄 Streamlit Frontend
│   ├── main.py                # Streamlit entry (chat, upload, payments)
│   ├── components/
│   │   ├── chat_ui.py
│   │   ├── upload_panel.py
│   │   ├── policy_comparator.py
│   │   └── payment_widget.py
│   ├── styles/
│   │   └── theme.css          # Custom CSS / Tailwind injection
│   └── utils/
│       └── session.py         # Session state helpers
│
├── backend/                   # ⚙️ Core Logic
│   ├── api.py                 # FastAPI microservice (webhooks, ingestion, etc.)
│   ├── config.py
│   ├── groq/
│   │   ├── groq_llm.py        # LangChain-compatible LLM wrapper
│   │   └── client.py          # Groq API connection + batching
│   ├── ingestion/
│   │   ├── ingest_docs.py     # Entry for doc ingestion
│   │   ├── parse_pdf.py       # Text extraction
│   │   ├── parse_image.py     # OCR fallback
│   │   ├── metadata_schema.py # Policy metadata model
│   │   └── llamaindex_pipeline.py # LlamaIndex → Chroma indexes
│   ├── index/
│   │   ├── chroma_client.py   # Initialize/query vector DB
│   │   └── retriever.py       # Top-k similarity retrieval
│   ├── chains/
│   │   ├── retrieval_chain.py # LangChain RetrievalQA w/ memory
│   │   ├── conversational_agent.py # Multi-turn chat logic
│   │   ├── tools.py           # Premium calculator, policy lookup, etc.
│   │   └── prompts.py         # Insurance tone + templates
│   ├── storage/
│   │   ├── audit_logger.py    # Append-only audit log
│   │   └── feedback_tracker.py# Logs user satisfaction
│   └── utils/
│       ├── hashing.py
│       ├── config_loader.py
│       └── sanitizers.py
│
├── data/
│   ├── uploads/               # Raw user uploads
│   ├── processed/             # Parsed / chunked documents
│   ├── chroma_db/             # Local vector store
│   └── samples/               # Example MSIG / Ancileo policies
│
├── logs/
│   ├── audit.log
│   └── interaction.log
│
├── deployment/
│   ├── Dockerfile             # Build Streamlit + FastAPI container
│   ├── start.sh               # Launch both services for Railway
│   └── railway.toml           # Railway deploy config
│
└── tests/
    ├── test_ingestion.py
    ├── test_retrieval.py
    ├── test_conversation.py
    └── test_end_to_end.py
```
### ✅ Streamlit Compatibility Note

- Streamlit does **not** require a special project layout.
- **Entry file:** \`app/main.py\`
- **Run:** \`streamlit run app/main.py\`
- You can add **multi-page** apps under \`app/pages/\`.
- **Backend (FastAPI)** can run separately or alongside Streamlit; the frontend calls it via HTTP.

---

## ⚡ Quickstart

### 1) Clone & Install
\`\`\`bash
git clone [https://github.com/SingHacks-2025/ancileo-msig.git](https://github.com/SingHacks-2025/ancileo-msig.git) insurance-jazzbot
cd insurance-jazzbot
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
\`\`\`
### 2) Configure Environment
Copy \`.env.example\` → \`.env\` and fill values:

\`\`\`env
# LLM & Tools
GROQ_API_KEY=...
TAVILY_API_KEY=...       # optional

# Retrieval / Index
CHROMA_PERSIST_DIR=./data/chroma_db

# App
APP_ENV=local
LOG_LEVEL=INFO
\`\`\`

### 3) Ingest Sample Policies (optional)
\`\`\`bash
python backend/ingestion/ingest_docs.py --input ./data/samples --out ./data/chroma_db
\`\`\`

### 4) Run Services
#### Option A – Separate terminals

\`\`\`bash
# Terminal 1 – FastAPI backend
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
\`\`\`

\`\`\`bash
# Terminal 2 – Streamlit frontend
streamlit run app/main.py
\`\`\`

#### Option B – Docker (Railway style)

\`\`\`bash
docker build -t insurance-jazzbot .
docker run -p 8501:8501 -p 8000:8000 --env-file .env insurance-jazzbot
\`\`\`

---

## 🔌 How It Works (High Level)
\`\`\`text
User → Streamlit UI (app/main.py)
    → Conversational Agent (backend/chains/conversational_agent.py)
    → Retrieval (backend/index/retriever.py → ChromaDB)
    → LLM (backend/groq/groq_llm.py → Groq LPU)
    → Tools (backend/chains/tools.py; e.g., premium calculator)
    → Response with rationale & policy matches
\`\`\`

### Core Flows
* **Ingestion:** PDFs/images → parse (PDF/OCR) → chunk → LlamaIndex → embeddings → Chroma
* **Chat:** Memory + RAG (RetrievalQA) + tools for policy lookup/premium calc
* **Audit:** Append-only logging for safety, plus feedback tracking

---

## 🧪 Testing
\`\`\`bash
pytest -q
# or individual modules:
pytest tests/test_ingestion.py -q
pytest tests/test_retrieval.py -q
pytest tests/test_conversation.py -q
pytest tests/test_end_to_end.py -q
\`\`\`

---

## 🧱 Design Choices
* **Groq** for ultra-low-latency inference (great chat UX)
* **Chroma** for local-first vector storage
* **LangChain + LlamaIndex** for flexible RAG pipelines
* **FastAPI** for modular APIs and clean integration
* **Streamlit** for rapid UI prototyping and easy sharing

---

## 🔐 Compliance & Safety Notes (Insurance Context)
* **\*\*❗ Do not output binding quotes;\*\* responses are illustrative suggestions only.**
* Add disclaimer in chat:
    > "This is an AI assistant; please verify final terms with MSIG/Ancileo."
* Mask **PII** in logs and redact sensitive uploads.
* Maintain append-only audit logs for traceability (\`backend/storage/audit_logger.py\`).

---

## ➡️ Quick Access & Important Links

| Links | Status |
| :--- | :--- |
| Schedule | Live |
| Challenge Statements | Coming Soon 🚀 |
| Mentor Gallery | Coming Soon 🚀 |
| Important Links | Coming Soon 🚀 |
| Team Formation Form | Coming Soon 🚀 |
| Submission Guide | Coming Soon 🚀 |

---

## ⚙️ Gearing Up for the Hackathon

### 1) Preparing for the Hackathon
* **Join Discord:** Ask questions, share ideas, find teammates in \`#team-matching\`.
* **Brainstorm:** Review challenge teasers and align on a direction.
* **Power Up:** Explore curated Hackathon Resources.

### 2) During the Hackathon
* **Get Hacking:** Build fast, iterate faster.
* **Book Mentors:** See Mentor Gallery.
* **Attend Workshops:** Join technical sessions to boost your project.

### 3) The Finishing Line
* **Submit by:** Nov 2, 2025, 11:00 AM SGT → see Submission Guide
* **Pitch & Judging:** Based on creativity, technical execution, and impact.
* **Finalists:** Announced for Singapore Fintech Festival (SFF)!
