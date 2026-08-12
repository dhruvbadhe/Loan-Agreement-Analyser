# System Execution Flow

Traces how control and data move between components during key interactions.

## 1. Document Ingestion Flow

```
[User Client] 
     │
     ▼ (POST /ingest)
[app/routers/ingest.py]
     │
     ▼ (extracts file stream)
[app/services/pdf_parser.py (parse_pdf)]
     │ ──► Returns extracted raw text and page_map
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
     │ ──► Stores text, embeddings, page numbers, & clause numbers
     ▼
[app/routers/ingest.py] ──► Returns Session ID & Chunk/Clause Metadata
```

## 2. Document Query Flow

```
[User Client]
     │
     ▼ (POST /query with session_id + question)
[app/routers/query.py]
     │
     ▼ (retrieves session collection)
[app/services/retriever.py (query_collection)]
     │ ──► Fetches top 5 relevant clauses matching question embedding
     ▼
[app/services/generator.py (generate_answer)]
     │ ──► Evaluates user question against context with custom citation prompt
     ▼
[app/routers/query.py] ──► Returns structured answer + page/clause citations
```
