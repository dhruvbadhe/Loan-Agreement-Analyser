# Technical Decisions Log

This log traces the "why" behind system design choices.

## 1. PersistentClient vs. In-Memory ChromaDB Client (2026-08-09)
- **What:** Replaced `chromadb.Client()` with `chromadb.PersistentClient()`.
- **Why:** During development and deployment, restarting the FastAPI server instantly cleared all in-memory vector data, causing active user sessions to fail. Standardizing on `PersistentClient` with a structured `CHROMA_DB_PATH` ensures user sessions survive service updates and container restarts.

## 2. Asynchronous RAGAS Evaluation (2026-08-09)
- **What:** Changed `/eval` from a synchronous `GET` endpoint to an asynchronous job queue (`POST /eval` and `GET /eval/{job_id}`).
- **Why:** Running RAGAS evaluations across a 15-question golden set with 3 metrics requires ~45 LLM requests. Doing this synchronously blocks the FastAPI server threads and leads to frontend/gateway timeout issues.

## 3. Background TTL Collection Reaper (2026-08-09)
- **What:** Added requirements for background session collection cleanup.
- **Why:** Manual cleanup on browser close or disconnect is unreliable. If a user exits mid-session, active collections remain in ChromaDB indefinitely, causing database bloat. A background TTL worker guarantees cleanup.

## 4. Transition to Groq and SentenceTransformers (2026-08-11)
- **What:** Switched from OpenAI API to Groq API (`llama-3.1-8b-instant`) for LLM tasks and local HuggingFace embeddings (`all-MiniLM-L6-v2`) via `sentence-transformers`.
- **Why:** To make the project accessible, cost-effective, and fully functional without requiring a paid OpenAI API key. Local embeddings run locally on CPU/GPU at zero cost, and Groq provides a high-speed, free-tier LLM API.

## 5. Immediate Raw File Cleanup (2026-08-12)
- **What:** Implemented a mandatory `finally` block in `POST /ingest` to delete uploaded PDF files immediately after they are parsed and embedded.
- **Why:** Adheres to user privacy constraints. Keeping raw financial contract PDFs on server disk raises security risks. Only vector representations in ChromaDB are preserved during the session.

## 6. Session Expiry 404 Handlers (2026-08-12)
- **What:** Intercepted ChromaDB `ValueError` in `POST /query` and converted it to a standard FastAPI HTTP 404 Exception.
- **Why:** When a session is purged or database files are deleted, ChromaDB raises a generic `ValueError` when querying. Translating this to an explicit HTTP 404 lets the frontend know exactly when to prompt the user to re-upload their document.

## 7. Streamlit Frontend Client (2026-08-12)
- **What:** Implemented a multi-tab Streamlit dashboard to interact with the backend API.
- **Why:** Streamlit allows building full-featured web UI forms, file uploads, chat history, and metric tables quickly in Python. It runs as a separate process and connects to the FastAPI backend using standard HTTP client calls.

## 8. Hybrid Search with Reciprocal Rank Fusion (2026-08-13)
- **What:** Combined Dense Retrieval (ChromaDB Vector Cosine Similarity) with Sparse Retrieval (BM25Okapi via `rank-bm25`) using Reciprocal Rank Fusion (RRF).
- **Why:** Dense embeddings capture high-level semantic meaning but often miss specific legal/financial keyword matches (e.g., "prepayment penalty", "EMI", "foreclosure"). BM25 catches exact keyword matches. Combining them via RRF delivers the best of both worlds, directly improving Context Precision and Faithfulness scores.

## 9. Tuning RRF Search Weights (2026-08-13)
- **What:** Configured Weighted RRF in `reciprocal_rank_fusion` with `dense_weight=0.8` and `sparse_weight=0.2`.
- **Why:** Initial unweighted RRF ensembling merged dense and sparse results equally, which caused keyword-heavy but semantically weak chunks from BM25 to displace coherent context paragraphs. Biasing RRF towards vector search (80%) preserves semantic grounding while retaining exact keyword matching (20%) as a ranking tie-breaker.

