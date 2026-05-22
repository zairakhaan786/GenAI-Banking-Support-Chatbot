<!-- Banner -->
<div align="center">

# 🏦 GenAI Banking Support Chatbot

### AI-Powered Customer Support using Retrieval-Augmented Generation (RAG)

[![CI](https://github.com/zairakhaan786/GenAI-Banking-Support-Chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/zairakhaan786/GenAI-Banking-Support-Chatbot/actions)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![ChromaDB](https://img.shields.io/badge/Vector_DB-ChromaDB-FF6B35)](https://www.trychroma.com)
[![LangChain](https://img.shields.io/badge/RAG-LangChain-1C3C3C)](https://langchain.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A production-ready AI banking assistant that answers customer queries about loans, credit cards, accounts, and banking policies — grounded in verified knowledge via RAG.**

[🚀 Live Demo](#deployment) · [📖 API Docs](http://localhost:8000/api/docs) · [🏗️ Architecture](docs/architecture.md)

</div>

---

## 📸 Screenshots

<table>
<tr>
<td width="50%">

**Chat Interface**
![Chat Interface](screenshots/chat_interface.png)

</td>
<td width="50%">

**Context-Aware Response**
![Context Response](screenshots/context_aware_response.png)

</td>
</tr>
<tr>
<td width="50%">

**Credit Card Query Response**
![Credit Cards](screenshots/credit_cards_response.png)

</td>
<td width="50%">

**Document Upload**
![Upload](screenshots/upload_interface.png)

</td>
</tr>
</table>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Full RAG Pipeline** | Document ingestion → chunking → embedding → retrieval → generation |
| 🧠 **Conversation Memory** | Session-aware context, resolves pronouns like "it", "that loan" |
| 📄 **Document Upload** | Index custom PDFs, TXTs, and DOCXs at runtime |
| 🗄️ **ChromaDB** | Persistent vector store with cosine similarity search |
| 🤖 **Multi-LLM Support** | Groq (free) → OpenAI → Google Gemini → Smart Fallback |
| 💡 **Zero-Key Mode** | Works without any API key using context-formatter fallback |
| 🎨 **Premium UI** | Dark glassmorphism theme, typing indicators, source citations |
| 📡 **REST API** | `/chat`, `/upload`, `/health` with OpenAPI docs |
| 🔄 **CI/CD** | GitHub Actions: lint, tests, Docker build, security scan |

---

## 🏗️ Architecture

```
Browser (Frontend)
   │  REST API (HTTP/JSON)
   ▼
FastAPI Backend
   │
   ├── POST /api/chat ──► RAG Pipeline
   │                          ├── 1. Session Memory (context-aware query)
   │                          ├── 2. Embedding Service (all-MiniLM-L6-v2, local)
   │                          ├── 3. ChromaDB Vector Search (top-k cosine similarity)
   │                          ├── 4. Prompt Builder (history + context + query)
   │                          └── 5. LLM Generation (Groq / OpenAI / Google / Fallback)
   │
   ├── POST /api/upload ─► Document Processor → ChromaDB
   └── GET  /api/health ─► Component status check
```

> Full architecture diagram: [docs/architecture.md](docs/architecture.md)

---

## 🧠 How I Implemented the RAG Flow

To make this chatbot intelligent and capable of answering specific banking queries, I designed a complete **Retrieval-Augmented Generation (RAG)** pipeline. Here is exactly how I built it to work behind the scenes:

1. **Document Ingestion & Chunking:** First, I take banking documents (like policies, FAQs, or TXT/PDF files) and process them. I split this text into smaller, meaningful "chunks" using LangChain's text splitters. This ensures we only feed the most relevant piece of text to the AI later, rather than a massive 50-page document.
2. **Generating Embeddings:** I used `sentence-transformers` (`all-MiniLM-L6-v2`) running locally to convert these text chunks into dense vector embeddings. I chose this approach so that the app doesn't have to rely on paid external APIs just to understand the semantic meaning of the text.
3. **Vector Storage (ChromaDB):** I store these vector embeddings in **ChromaDB**. When a user asks a question, ChromaDB performs a rapid mathematical cosine similarity search to find the top 5 chunks of text that most closely match the meaning of the user's question.
4. **Context-Aware Memory:** I implemented a session memory system. If a user asks "What are the interest rates for a personal loan?" and then follows up with "What is the maximum tenure for *it*?", my pipeline resolves the pronoun "it" using previous chat history before querying the vector database.
5. **LLM Generation:** Finally, I take the user's question, the conversation history, and the highly relevant context retrieved from ChromaDB, and I pass it all into a Large Language Model (like Groq's Llama 3). The LLM synthesizes this raw data into a natural, conversational, and highly accurate response.

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| RAG Framework | LangChain, LangChain-Core |
| Embeddings | `sentence-transformers` — `all-MiniLM-L6-v2` (local, free) |
| Vector Database | ChromaDB (persistent) |
| LLM | Groq `llama3-8b-8192` / OpenAI / Google Gemini / Fallback |
| Document Processing | pypdf, python-docx |
| Frontend | Vanilla HTML5, CSS3, JavaScript |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Deployment | Render / Railway / Docker |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- (Optional) Free Groq API key from [console.groq.com](https://console.groq.com)

### 1. Clone & Setup
```bash
git clone https://github.com/zairakhaan786/GenAI-Banking-Support-Chatbot.git
cd GenAI-Banking-Support-Chatbot/backend

# Create virtual environment
python3 -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Optional: add GROQ_API_KEY=your_key to .env for full LLM responses
```

### 2. Run
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** — the banking knowledge base loads automatically on first startup (~30-60s for model download).

### 3. Docker
```bash
# From project root
docker-compose up --build
```

---

## 📡 API Reference

### `POST /api/chat`
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are personal loan interest rates?", "session_id": "sess_001"}'
```
```json
{
  "answer": "Personal loan interest rates range from 10.5% to 24% per annum...",
  "sources": [{"content": "...", "score": 0.87, "source": "banking_knowledge_base.txt"}],
  "model_used": "groq/llama3-8b-8192",
  "retrieval_count": 5
}
```

### `POST /api/upload`
```bash
curl -X POST http://localhost:8000/api/upload -F "file=@loan_policy.pdf"
```

### `GET /api/health`
```bash
curl http://localhost:8000/api/health
```

📘 **Interactive docs:** http://localhost:8000/api/docs

---

## 📁 Project Structure

```
GenAI-Banking-Support-Chatbot/
├── backend/
│   ├── app/
│   │   ├── config.py              # Pydantic settings & env config
│   │   ├── main.py                # FastAPI app, lifespan, routing
│   │   ├── models/schemas.py      # Request/response models
│   │   ├── routes/
│   │   │   ├── chat.py            # POST /api/chat
│   │   │   ├── upload.py          # POST /api/upload
│   │   │   └── health.py          # GET /api/health
│   │   ├── services/
│   │   │   ├── rag_pipeline.py    # Core RAG orchestration
│   │   │   ├── vector_store.py    # ChromaDB integration
│   │   │   ├── embeddings.py      # sentence-transformers
│   │   │   ├── llm_service.py     # Multi-provider LLM
│   │   │   ├── document_processor.py  # PDF/TXT/DOCX ingestion
│   │   │   └── memory.py          # Session conversation memory
│   │   └── utils/logger.py        # Loguru structured logging
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── run.py
│   └── .env.example
├── frontend/
│   ├── index.html                 # Chatbot SPA
│   ├── css/style.css              # Dark glassmorphism theme
│   └── js/app.js                  # Chat logic, upload, sessions
├── data/
│   └── banking_knowledge_base.txt # Pre-built banking knowledge (~49 chunks)
├── docs/
│   └── architecture.md            # Detailed architecture + flow diagrams
├── deployment/
│   ├── render.yaml                # Render deployment config
│   └── DEPLOY.md                  # Step-by-step deployment guide
├── screenshots/                   # UI screenshots for documentation
├── .github/workflows/ci.yml       # GitHub Actions CI pipeline
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## ☁️ Deployment

### Render Deployment

I deployed this application using Render. Since persistent disks require a paid plan on Render, I configured ChromaDB to use the ephemeral disk for the free deployment. This means the knowledge base re-indexes on each restart, which works perfectly for demonstration purposes.

1. Create a **Web Service** on [render.com](https://render.com)
2. Connect this repository.
3. Set the Environment to `Python`.
4. Render will automatically detect the `render.yaml` configuration at the root of the repository.
5. Add your `GROQ_API_KEY` in the Render environment variables dashboard.

**🔗 Live Demo:** `https://genai-banking-chatbot.onrender.com`

---



## 🔮 Future Improvements

- **Streaming responses** — Server-Sent Events for real-time token streaming
- **Redis session store** — Replace in-memory sessions for multi-instance deployment
- **Re-ranking** — Cross-encoder reranking for improved retrieval precision
- **Authentication** — JWT-based user auth with per-user knowledge bases
- **Query analytics** — Track common questions to improve knowledge base
- **Multi-language** — Support queries in regional Indian languages

---

## 📄 License

MIT © [Zaira Khan](https://github.com/zairakhaan786)

---

<div align="center">
Built with ❤️ using FastAPI, LangChain, ChromaDB & sentence-transformers
</div>
