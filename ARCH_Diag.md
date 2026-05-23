# System Architecture: GenAI Banking Support Chatbot

This diagram illustrates the end-to-end data flow of the Banking Support Chatbot, detailing how the Frontend, Backend, Vector Database, and LLM Generation interact during a user query.

```mermaid
graph TD
    %% Styling
    classDef frontend fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:#fff
    classDef backend fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    classDef rag fill:#8b5cf6,stroke:#7c3aed,stroke-width:2px,color:#fff
    classDef db fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff
    classDef llm fill:#ec4899,stroke:#db2777,stroke-width:2px,color:#fff
    classDef user fill:#64748b,stroke:#475569,stroke-width:2px,color:#fff

    %% Components
    User((🧑‍💻 User)):::user

    subgraph Frontend [🌐 Frontend Interface]
        UI[Web Chat Interface\nHTML/CSS/JS]:::frontend
    end

    subgraph Backend [⚙️ FastAPI Backend]
        API[API Router\n/api/chat]:::backend
        MEM[Conversation Memory\nSession Tracking]:::backend
    end

    subgraph RAG_Pipeline [🧠 RAG Pipeline]
        QUERY[Query Reformulation\nContext-Aware]:::rag
        EMBED[Embedding Model\nMiniLM-L6-v2]:::rag
        RETRIEVE[Similarity Search\nTop-K Retrieval]:::rag
        PROMPT[Prompt Assembly\nContext + History + Query]:::rag
    end

    subgraph Storage [🗄️ Storage Layer]
        VDB[(ChromaDB\nVector Store)]:::db
        DOCS[Banking Documents\nPDFs, TXT]:::db
    end

    subgraph LLM_Generation [🤖 LLM Generation]
        LLM[Groq / OpenAI\nMixtral / Llama3]:::llm
    end

    %% Data Flow
    User -- "1. Asks question\n(e.g., 'What are the rates?')" --> UI
    UI -- "2. POST /api/chat" --> API
    
    API -- "3. Retrieve History" --> MEM
    MEM -- "4. Resolve Pronouns" --> QUERY
    
    QUERY -- "5. Generate Embeddings" --> EMBED
    EMBED -- "6. Search Vector DB" --> RETRIEVE
    RETRIEVE -- "7. Fetch Nearest Chunks" --> VDB
    VDB -- "8. Return Top-K Context" --> RETRIEVE
    
    DOCS -. "Pre-indexed offline" .-> VDB
    
    RETRIEVE -- "9. Inject Context" --> PROMPT
    MEM -- "10. Inject History" --> PROMPT
    PROMPT -- "11. Send Augmented Prompt" --> LLM
    
    LLM -- "12. Generate Grounded Response" --> API
    API -- "13. Return JSON" --> UI
    UI -- "14. Display Answer" --> User
```
