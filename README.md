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
insurance-jazzbot/
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


