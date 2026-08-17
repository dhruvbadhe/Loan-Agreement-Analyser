# System Execution Flow

Traces how control and data move between components during key interactions.

## 1. Document Ingestion Flow

```
[Streamlit Frontend Container]
     │
     ▼ (POST /ingest)
[FastAPI Backend Container (app/routers/ingest.py)]
     │
     ▼ (extracts file stream)
[app/services/pdf_parser.py (parse_pdf)]
     │ ──► Returns extracted text and page_map
     ▼
[app/services/chunker.py (chunk_by_clause)]
     │ ──► Splits text on clause boundaries; returns clause list
     ▼
[app/services/embedder.py (embed_clauses)]
     │ ──► Generates local SentenceTransformer embeddings for each clause text
     ▼
[app/services/retriever.py (get_collection)]
     │ ──► Creates persistent, session-isolated collection
     ▼
[app/services/retriever.py (add_documents)]
     │ ──► Stores text, embeddings, page numbers, & clause numbers in mounted db volume
     ▼
[app/routers/ingest.py] ──► Returns Session ID & Chunk/Clause Metadata
```

## 2. Document Hybrid Query Flow

```
[Streamlit Frontend Container]
     │
     ▼ (POST /query with session_id + question)
[FastAPI Backend Container (app/routers/query.py)]
     │
     ▼ (retrieves session collection)
[app/services/retriever.py (query_session_collection)]
     │
     ├──► 1. Calls expand_query to get alternative search queries via Groq
     ├──► 2. Fetches all document chunks in collection
     ├──► 3. Generates local query embeddings for all query variants
     │
     ├──► 4. DENSE SEARCH: ChromaDB vector query matching (Cosine Similarity)
     ├──► 5. SPARSE SEARCH: Tokenizes and runs BM25 query in-memory
     │
     ▼
[app/services/retriever.py (reciprocal_rank_fusion)]
     │ ──► Ensembles and reranks dense & sparse results using weighted RRF
     ▼
[app/services/generator.py (generate_answer)]
     │ ──► Evaluates user question against context with custom citation prompt
     ▼
[app/routers/query.py] ──► Returns structured answer + page/clause citations to Frontend
```
