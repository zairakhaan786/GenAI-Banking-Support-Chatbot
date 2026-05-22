# Architecture — GenAI Banking Support Chatbot

## System Overview

The system is a three-layer architecture: a browser-based frontend, a FastAPI backend, and a persistent vector store backed by ChromaDB. The backend orchestrates the full RAG pipeline on every chat request.

---

## Component Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                     BROWSER (Frontend)                               │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │  index.html + css/style.css + js/app.js                       │   │
│  │  • Session management (sessionStorage)                        │   │
│  │  • Chat interface with typing indicator                       │   │
│  │  • File upload (drag & drop)                                  │   │
│  │  • Source citation modal                                      │   │
│  │  • Quick action shortcuts                                     │   │
│  └───────────────────────┬───────────────────────────────────────┘   │
└────────────────────────────┼─────────────────────────────────────────┘
                             │ HTTP REST (JSON)
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND                                  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Routing Layer (app/routes/)                                   │  │
│  │  POST /api/chat  │  POST /api/upload  │  GET /api/health       │  │
│  └──────────────────────────┬─────────────────────────────────────┘  │
│                             │                                        │
│  ┌──────────────────────────▼─────────────────────────────────────┐  │
│  │  RAG Pipeline (app/services/rag_pipeline.py)                   │  │
│  │                                                                │  │
│  │  1. SESSION MEMORY                                             │  │
│  │     └─ Get conversation history for session_id                │  │
│  │     └─ Build contextual query (pronoun resolution)            │  │
│  │                                                                │  │
│  │  2. EMBEDDING SERVICE (app/services/embeddings.py)            │  │
│  │     └─ sentence-transformers: all-MiniLM-L6-v2               │  │
│  │     └─ Local execution, no API key required                   │  │
│  │                                                                │  │
│  │  3. VECTOR STORE (app/services/vector_store.py)               │  │
│  │     └─ ChromaDB persistent client                             │  │
│  │     └─ Cosine similarity search, top-k retrieval              │  │
│  │     └─ Returns (Document, relevance_score) pairs              │  │
│  │                                                                │  │
│  │  4. PROMPT BUILDER                                             │  │
│  │     └─ Injects: history + retrieved context + user query      │  │
│  │     └─ Structured prompt with chunk citations                 │  │
│  │                                                                │  │
│  │  5. LLM SERVICE (app/services/llm_service.py)                 │  │
│  │     └─ Provider priority: Groq → OpenAI → Google → Fallback  │  │
│  │     └─ Fallback: smart context formatter (no API key)         │  │
│  │                                                                │  │
│  │  6. RESPONSE + MEMORY UPDATE                                   │  │
│  │     └─ Return answer + source citations                       │  │
│  │     └─ Add turn to session memory                             │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Document Processor (app/services/document_processor.py)     │    │
│  │  • PDF extraction (pypdf)                                     │    │
│  │  • TXT reading                                                │    │
│  │  • DOCX parsing (python-docx)                                │    │
│  │  • RecursiveCharacterTextSplitter (chunk=600, overlap=80)    │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     PERSISTENCE LAYER                                │
│                                                                      │
│  ┌──────────────────────────┐   ┌────────────────────────────────┐   │
│  │  ChromaDB                │   │  In-Memory Session Store        │   │
│  │  ./chroma_db/            │   │  (Redis-ready interface)        │   │
│  │  • Persistent storage    │   │  • Per-session message history  │   │
│  │  • banking_knowledge_base│   │  • Auto-expiry (60 min)         │   │
│  │  • User-uploaded docs    │   │  • Thread-safe (Lock)           │   │
│  └──────────────────────────┘   └────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## RAG Pipeline — Detailed Flow

```
User Query: "What is the interest rate for it?"
                │
                ▼
    ┌───────────────────────┐
    │   Session Memory      │
    │   Previous: "Tell me  │
    │   about credit cards" │
    └──────────┬────────────┘
               │ Contextual Query:
               │ "Tell me about credit cards
               │  What is the interest rate for it?"
               ▼
    ┌───────────────────────┐
    │   Embedding Service   │
    │   all-MiniLM-L6-v2   │
    │   → 384-dim vector    │
    └──────────┬────────────┘
               │
               ▼
    ┌───────────────────────┐
    │   ChromaDB Search     │
    │   Cosine similarity   │
    │   Top-5 chunks        │
    └──────────┬────────────┘
               │ Returns: [(doc, 0.87), (doc, 0.81), ...]
               ▼
    ┌───────────────────────┐
    │   Prompt Builder      │
    │   System + History    │
    │   + Context + Query   │
    └──────────┬────────────┘
               │
               ▼
    ┌───────────────────────┐
    │   LLM Generation      │
    │   Groq / OpenAI /     │
    │   Google / Fallback   │
    └──────────┬────────────┘
               │
               ▼
    ┌───────────────────────┐
    │   Response            │
    │   + Source Citations  │
    │   + Memory Update     │
    └───────────────────────┘
```

---

## Technology Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Vector DB | ChromaDB | Free, persistent, easy setup, LangChain native |
| Embeddings | all-MiniLM-L6-v2 | Free, local, fast, 384-dim, good semantic quality |
| Primary LLM | Groq (llama3-8b-8192) | Free tier, very fast inference (~200 tokens/sec) |
| Framework | FastAPI | Async, auto OpenAPI docs, type-safe |
| Text splitting | RecursiveCharacterTextSplitter | Preserves semantic boundaries |
| Session storage | In-memory dict | Simple, fast; Redis can be swapped in for production |

---

## Data Flow for Document Upload

```
User uploads PDF/TXT/DOCX
         │
         ▼
   File validation
   (type, size check)
         │
         ▼
   Save to ./uploads/
         │
         ▼
   DocumentProcessor
   • Extract text
   • Clean whitespace
         │
         ▼
   RecursiveCharacterTextSplitter
   chunk_size=600, overlap=80
         │
         ▼
   EmbeddingService.embed_documents()
         │
         ▼
   ChromaDB.add_documents()
         │
         ▼
   Return: chunks_indexed, collection_total
```

---

## Deployment Architecture (Render)

```
GitHub Repository
       │
       │  git push (triggers)
       ▼
GitHub Actions CI
• Lint (ruff)
• Tests
• Docker build validation
       │
       ▼ (on main branch)
Render Web Service
• Build: pip install -r requirements.txt
• Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
• Persistent disk: /chroma_db (vector store)
• Environment vars: GROQ_API_KEY, LLM_PROVIDER
```

---

## Security Considerations

- No secrets or API keys hardcoded in source files
- All sensitive config via environment variables / `.env` (gitignored)
- File upload: size limit (20MB), type whitelist (pdf, txt, docx)
- UUID-prefixed filenames for uploads to prevent path traversal
- Non-root Docker user (`bankbot`)
- CORS configurable via `ALLOWED_ORIGINS` env var
