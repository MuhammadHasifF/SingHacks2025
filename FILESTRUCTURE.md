insurance-jazzbot/
│
├── README.md                          # keep Ancileo × MSIG context + this integration doc
├── requirements.txt
├── .env.example
├── .gitignore
│
├── app/                               # 🪄 Streamlit Frontend
│   ├── main.py                        # Streamlit entry (chat, upload, payments)
│   ├── components/
│   │   ├── chat_ui.py
│   │   ├── upload_panel.py
│   │   ├── policy_comparator.py
│   │   └── payment_widget.py
│   ├── styles/                        # Custom CSS or Tailwind injection
│   │   └── theme.css
│   └── utils/session.py
│
├── backend/                           # ⚙️ Core Logic
│   ├── api.py                         # FastAPI microservice (for webhooks, ingestion, etc.)
│   ├── config.py
│   ├── groq/
│   │   ├── groq_llm.py                # LangChain-compatible LLM wrapper
│   │   └── client.py                  # Handles API connection + batching
│   ├── ingestion/
│   │   ├── ingest_docs.py             # Entry point for doc ingestion
│   │   ├── parse_pdf.py               # Text extraction
│   │   ├── parse_image.py             # OCR fallback
│   │   ├── metadata_schema.py         # Policy metadata model
│   │   └── llamaindex_pipeline.py     # Uses LlamaIndex to create Chroma indexes
│   ├── index/
│   │   ├── chroma_client.py           # Initialize/query vector DB
│   │   └── retriever.py               # Query top-k chunks by similarity
│   ├── chains/
│   │   ├── retrieval_chain.py         # LangChain RetrievalQA w/ memory
│   │   ├── conversational_agent.py    # Handles multi-turn chat logic
│   │   ├── tools.py                   # Premium calculator, policy lookup, etc.
│   │   └── prompts.py                 # Custom insurance tone + templates
│   ├── storage/
│   │   ├── audit_logger.py            # Immutable log (append-only)
│   │   └── feedback_tracker.py        # Logs user satisfaction
│   └── utils/
│       ├── hashing.py
│       ├── config_loader.py
│       └── sanitizers.py
│
├── data/
│   ├── uploads/                       # Raw user uploads
│   ├── processed/                     # Parsed / chunked documents
│   ├── chroma_db/                     # Local vector store
│   └── samples/                       # Example MSIG / Ancileo policies
│
├── logs/
│   ├── audit.log
│   └── interaction.log
│
├── deployment/
│   ├── Dockerfile                     # Build Streamlit + FastAPI container
│   ├── start.sh
│   └── railway.toml                   # Railway deploy config
│
└── tests/
    ├── test_ingestion.py
    ├── test_retrieval.py
    ├── test_conversation.py
    └── test_end_to_end.py
