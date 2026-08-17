# System Architecture Map

## Overview
The Loan Agreement Analyser is a specialized Retrieval-Augmented Generation (RAG) system with clause-boundary parsing, session-scoped vector databases, hybrid retrieval (dense + sparse), query expansion, and quantitative benchmark evaluation.

```mermaid
graph TD
    User([User Client]) -->|PDF Upload /ingest| Frontend[Streamlit Frontend Container]
    Frontend -->|HTTP Request| API[FastAPI Backend Container]
    User -->|Ask Question /query| Frontend

    subgraph Backend Services Container
        API --> Chunker[Clause Chunker]
        API --> Parser[PDF Parser]
        API --> Embedder[Embedder Service]
        API --> Retriever[Session-Scoped Retriever]
        API --> Generator[Response Generator]
        API --> Evaluator[Dynamic LLM Evaluator]
    end

    subgraph Hybrid Retrieval Engine
        Retriever -->|Dense Search| Chroma[(ChromaDB Volume)]
        Retriever -->|Sparse Search| BM25[In-Memory BM25Okapi]
        Chroma --> RRF[Reciprocal Rank Fusion]
        BM25 --> RRF
        RRF -->|Combined Chunks| Generator
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
4. **Retriever Service (`app/services/retriever.py`):** Interfaces with ChromaDB `PersistentClient` and `rank-bm25` in-memory index, ensembling results using Reciprocal Rank Fusion (RRF).
5. **Generator Service (`app/services/generator.py`):** Formulates prompts with grounding context, executes query expansion, and calls `llama-3.1-8b-instant` via Groq.
6. **Evaluator Service (`eval/run_eval.py`):** Dynamically generates synthetic test questions from database chunks and evaluates faithfulness/relevancy using Groq.
