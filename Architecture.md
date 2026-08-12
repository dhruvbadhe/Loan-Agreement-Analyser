# System Architecture Map

## Overview
The Loan Agreement Analyser is a specialized Retrieval-Augmented Generation (RAG) system with clause-boundary parsing, session-scoped vector databases, and quantitative benchmark evaluation.

```mermaid
graph TD
    User([User Client]) -->|PDF Upload /ingest| API[FastAPI Server]
    User -->|Ask Question /query| API
    User -->|Trigger Evaluation /eval| API

    subgraph Backend Services
        API --> Chunker[Clause Chunker]
        API --> Parser[PDF Parser]
        API --> Embedder[Embedder Service]
        API --> Retriever[Session-Scoped Retriever]
        API --> Generator[Response Generator]
        API --> Evaluator[RAGAS Evaluator]
    end

    subgraph Storage
        Retriever -->|CRUD collections| Chroma[(Persistent ChromaDB)]
    end
    
    subgraph Local Hardware
        Embedder -->|all-MiniLM-L6-v2| HF[Local SentenceTransformers]
    end

    subgraph LLM Provider (Groq)
        Generator -->|llama-3.1-8b-instant| Groq[Groq API]
        Evaluator -->|eval metrics| Groq
    end
```

## Service Components
1. **API Layer (`app/main.py` & `app/routers/`):** Exposes FastAPI endpoints for document ingestion, session querying, session teardown, and benchmarking.
2. **PDF Parser Service (`app/services/pdf_parser.py`):** Wraps PyMuPDF for document page parsing and line-offset mapping.
3. **Clause Chunker Service (`app/services/chunker.py`):** Uses layout indicators and numbering regex to parse legal clauses cleanly.
4. **Retriever Service (`app/services/retriever.py`):** Interfaces with ChromaDB `PersistentClient`, isolating user data using unique session ID namespaces.
5. **Generator Service (`app/services/generator.py`):** Formulates prompts with grounding context and calls `llama-3.1-8b-instant` via Groq.
6. **RAGAS Evaluator Service (`app/services/evaluator.py`):** Manages offline/async test evaluation of the pipeline compared to a naive recursive chunker.
