# Session Handover Notes

## Current Progress
We have completed writing the core RAG system for the Loan Agreement Analyser using Groq (`llama-3.1-8b-instant`) and local SentenceTransformers (`all-MiniLM-L6-v2`).

All components have been designed, reviewed, and manually typed by the user:
1. **Config (`app/core/config.py`):** Holds settings and Groq API configs.
2. **PDF Parser (`app/services/pdf_parser.py`):** Page-by-page parser mapping page offsets.
3. **Clause Chunker (`app/services/chunker.py`):** Layout-resilient chunker using regex lookaheads.
4. **Local Embedder (`app/services/embedder.py`):** Encodes text locally to 384-dimensional vectors.
5. **Retriever (`app/services/retriever.py`):** Interfaces with ChromaDB PersistentClient using session-isolated collections.
6. **Generator (`app/services/generator.py`):** Prompts Groq and parses responses with citations.
7. **Routers (`app/routers/`):** Routers for Ingest (`POST /ingest`), Query (`POST /query`), and Session Management (`DELETE /session/{session_id}`).
8. **Entrypoint (`app/main.py`):** Runs FastAPI app with CORS.
9. **Streamlit App (`frontend/app.py`):** Tabbed interface with chat history, file uploads, sources expansion, and session purging.

## Next Steps / How to Run
1. Start the FastAPI backend:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. Start the Streamlit frontend in a separate terminal:
   ```bash
   python -m streamlit run frontend/app.py
   ```
3. Open `http://localhost:8501`, upload a sample loan agreement PDF, and query it.
