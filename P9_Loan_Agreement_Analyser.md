# P9: Loan Agreement Analyser — Complete Project Plan

## What It Is

Users upload their personal loan/home loan agreement PDF and ask plain English questions about it. The system finds the exact clause, answers the question, and cites the clause number and page.

**Core problem:** Banks give 50-page legal agreements. People sign without reading. Buried clauses cost them money later.

**Example queries:**
- "What is my prepayment penalty in year 2?"
- "Can the bank change my interest rate without notice?"
- "What happens if I miss 2 EMIs?"
- "What documents do I need to foreclose this loan?"

---

## Technical Differentiators

### 1. Clause-Boundary Chunking
Loan agreements have numbered clauses (3.1, 3.2, 4.1). Vanilla RAG splits by character count — a chunk might contain half of clause 3.1 and half of clause 3.2, losing the legal meaning of both.

Your chunker splits on clause boundaries using regex. Every chunk is always one complete legal clause. Retrieved chunks are always coherent and citable.

```python
# Standard chunking (bad for legal docs)
chunk = "...interest rate shall be revised. 4.2 The borrower shall maintain"

# Clause-boundary chunking (what you build)
chunk_1 = "4.1 The bank reserves the right to revise the interest rate with 7 days written notice to the borrower."
chunk_2 = "4.2 The borrower shall maintain a minimum balance of..."
```

### 2. Session-Scoped Vector Store
Each user's document creates a temporary ChromaDB collection. It gets cleared after the session ends or via background TTL cleanup. No mixing of one user's loan document with another's.

This is a real production decision — in a multi-user system, you cannot let User A's loan clauses bleed into User B's answers.

```python
# Each session gets its own isolated collection
collection_name = f"loan_{session_id}"  # e.g., loan_a3f9b2
# Cleared on session end via DELETE /session/{session_id} or auto-reaped by TTL scheduler
```

### 3. RAGAS Eval Pipeline with Before/After Comparison
Build a golden test set of 15 Q&A pairs from a sample loan agreement. Run naive RAG (character chunking) vs your RAG (clause chunking). Show the delta.

**This is the money shot in your README:**
| Metric | Naive RAG | Clause-Chunked RAG |
|---|---|---|
| Faithfulness | 0.71 | 0.89 |
| Context Precision | 0.64 | 0.83 |
| Answer Relevancy | 0.78 | 0.91 |

---

## System Design

### Core Query Flow
```
User Question
      ↓
FastAPI /query endpoint
      ↓
ChromaDB (session-scoped collection)
      ↓
Clause-level retrieval (top 5 chunks)
      ↓
GPT-4o-mini with citation prompt
      ↓
Answer + Clause citations (clause number + page)
```

### Ingestion Flow
```
PDF Upload (POST /ingest)
      ↓
PyMuPDF — extract raw text + page numbers
      ↓
Clause Boundary Chunker (regex on numbered clauses)
      ↓
Each chunk tagged: {clause_id, page_number, section}
      ↓
text-embedding-3-small → embeddings
      ↓
ChromaDB session-scoped collection
      ↓
Return: {session_id, chunk_count, clauses_found}
```

---

## Project Structure

```
loan-rag/
├── app/
│   ├── main.py                  # FastAPI app, router registration
│   ├── routers/
│   │   ├── ingest.py            # POST /ingest
│   │   ├── query.py             # POST /query
│   │   ├── session.py           # DELETE /session/{id}
│   │   └── eval.py              # GET /eval
│   ├── services/
│   │   ├── pdf_parser.py        # PyMuPDF extraction + page tracking
│   │   ├── chunker.py           # Clause-boundary chunking logic
│   │   ├── embedder.py          # OpenAI embeddings wrapper
│   │   ├── retriever.py         # ChromaDB query, session scoping
│   │   ├── generator.py         # LLM call + citation formatting
│   │   └── evaluator.py         # RAGAS pipeline
│   ├── core/
│   │   ├── config.py            # Env vars (API keys, model names)
│   │   └── vectorstore.py       # ChromaDB client singleton
│   └── Dockerfile
├── frontend/
│   ├── app.py                   # Streamlit app
│   └── Dockerfile
├── eval/
│   ├── golden_set.json          # 15 hand-crafted Q&A pairs
│   └── run_eval.py              # Naive vs clause-chunked comparison
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Endpoints

| Method | Endpoint | What it does |
|---|---|---|
| POST | `/ingest` | Upload PDF, chunk, embed, store in session collection |
| POST | `/query` | Ask question against session collection |
| DELETE | `/session/{session_id}` | Clear session vector store |
| POST | `/eval` | Trigger async background RAGAS evaluation on golden test set |
| GET | `/eval/{job_id}` | Get status/metrics of a RAGAS evaluation job |
| GET | `/health` | Health check |

### Request/Response Examples

**POST /ingest**
```json
// Request (multipart form)
file: loan_agreement.pdf

// Response
{
  "session_id": "a3f9b2",
  "chunks_created": 47,
  "clauses_found": 43,
  "pages": 52
}
```

**POST /query**
```json
// Request
{
  "session_id": "a3f9b2",
  "question": "What is the prepayment penalty?"
}

// Response
{
  "answer": "Under clause 6.3, prepayment before 36 months incurs a penalty of 2% on the outstanding principal. After 36 months, no prepayment charges apply.",
  "citations": [
    {
      "clause_id": "6.3",
      "page": 18,
      "text": "Prepayment before completion of 36 months from disbursement date shall attract a prepayment charge of 2% on the outstanding principal amount..."
    }
  ]
}
```

---

## Key Implementation Details

### Clause Boundary Chunker (`services/chunker.py`)

```python
import re
from typing import List, Dict

def chunk_by_clause(text: str, page_map: Dict[int, int]) -> List[Dict]:
    """
    Splits loan agreement text on numbered clause boundaries.
    Handles formats: 1., 1.1, 1.1.1, (a), (i)
    """
    clause_pattern = re.compile(
        r'(?=^\s*(?:\d+\.(?:\d+\.?)*|\([a-z]\)|\([ivxlc]+\))\s)',
        re.MULTILINE
    )
    
    splits = clause_pattern.split(text)
    chunks = []
    
    for split in splits:
        if len(split.strip()) < 20:  # skip noise
            continue
        
        clause_id = extract_clause_id(split)
        page = find_page(split, page_map)
        
        chunks.append({
            "text": split.strip(),
            "clause_id": clause_id,
            "page": page,
            "char_count": len(split)
        })
    
    return chunks
```

### Session-Scoped Vector Store (`services/retriever.py`)

```python
import chromadb
import os

# Use PersistentClient to persist state across container/server restarts
DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
client = chromadb.PersistentClient(path=DB_PATH)

def get_collection(session_id: str):
    return client.get_or_create_collection(
        name=f"loan_{session_id}",
        metadata={"hnsw:space": "cosine"}
    )

def delete_session(session_id: str):
    try:
        client.delete_collection(f"loan_{session_id}")
    except ValueError:
        pass  # Collection already deleted or does not exist
```

### Citation Prompt (`services/generator.py`)

```python
SYSTEM_PROMPT = """
You are a loan agreement analyst. Answer questions using ONLY the provided clauses.

Rules:
- Always cite the clause number (e.g., "Under clause 6.3...")
- Always mention the page number
- If the answer is not in the provided clauses, say "This is not covered in the uploaded document"
- Never infer or assume information not present in the clauses
- Quote the exact clause text when relevant
"""
```

---

## Frontend (Streamlit)

Three tabs:

**Tab 1 — Upload**
- Drag and drop PDF
- Show ingestion stats (clauses found, pages, chunks)
- Display sample clauses found

**Tab 2 — Ask**
- Chat interface
- Each answer shows the clause citation and page number
- Option to see raw clause text

**Tab 3 — Eval**
- Button to run RAGAS evaluation
- Show metrics table: naive RAG vs clause-chunked RAG
- Bar chart of improvement

---

## Tech Stack

| Component | Tool | Why |
|---|---|---|
| PDF parsing | PyMuPDF | Fast, page-level text extraction |
| Chunking | Custom regex chunker | Clause-boundary awareness |
| Embeddings | `text-embedding-3-small` | Cheap, good quality |
| Vector DB | ChromaDB | In-process, no infra needed |
| LLM | GPT-4o-mini | Cheap, good instruction following |
| Backend | FastAPI | Async, clean |
| Frontend | Streamlit | Fast to ship |
| Eval | RAGAS | Faithfulness + Context Precision |
| Deployment | Docker Compose | API + frontend as separate services |

---

## Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: ./app
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./uploads:/app/uploads

  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
    depends_on:
      - api
    environment:
      - API_URL=http://api:8000
```

---

## RAGAS Evaluation Setup

### Golden Test Set (`eval/golden_set.json`)
Hand-craft 15 Q&A pairs from a real/sample loan agreement:

```json
[
  {
    "question": "What is the prepayment penalty before 3 years?",
    "ground_truth": "2% on outstanding principal",
    "relevant_clause": "6.3"
  },
  {
    "question": "How many days notice does the bank give before changing interest rate?",
    "ground_truth": "7 days written notice",
    "relevant_clause": "4.1"
  }
  // ... 13 more
]
```

### Metrics to track
- **Faithfulness** — is the answer grounded in retrieved clauses?
- **Context Precision** — are retrieved clauses relevant to the question?
- **Answer Relevancy** — does the answer actually address the question?

Run both naive RAG and clause-chunked RAG on the same set. The delta is your proof of engineering.

---

## Build Timeline

### Day 1 — Ingestion Pipeline
- [ ] PyMuPDF PDF parser with page tracking
- [ ] Naive chunker first (RecursiveCharacterTextSplitter)
- [ ] ChromaDB setup, basic embedding + storage
- [ ] POST /ingest working end to end
- [ ] POST /query working with basic retrieval

**Goal:** Upload a PDF and get an answer, ugly is fine.

### Day 2 — The Two Differentiators
- [ ] Build clause-boundary chunker with layout/structural resilience (regex fallback), replace naive chunker
- [ ] Add session scoping to ChromaDB collections using `PersistentClient`
- [ ] Add DELETE /session endpoint & background TTL cleanup scheduler for orphaned collections
- [ ] Tune citation system prompt
- [ ] Verify clause citations are accurate

**Goal:** Answers cite specific clause numbers and pages.

### Day 3 — Eval + Frontend
- [ ] Build golden test set (15 Q&A pairs)
- [ ] Implement async background tasks for `/eval` (POST to start, GET status) to prevent timeouts
- [ ] Run RAGAS on naive RAG, save scores
- [ ] Run RAGAS on clause-chunked RAG, save scores
- [ ] Build Streamlit frontend (3 tabs)
- [ ] Wire frontend to FastAPI

**Goal:** Working UI + eval numbers in hand.

### Day 4 — Polish + Docker
- [ ] Docker Compose setup
- [ ] Error handling (bad PDF, empty doc, session not found)
- [ ] README with architecture diagram + RAGAS comparison table
- [ ] Clean up code, add docstrings
- [ ] Record demo video (2 min)

**Goal:** Ship-ready, interview-ready.

---

## README Must-Haves

Your README is what a recruiter sees before your code. It needs:

1. **One-line description** — what problem, what solution
2. **Architecture diagram** — ingestion flow + query flow (draw.io or excalidraw)
3. **RAGAS comparison table** — naive vs clause-chunked, with actual numbers
4. **Setup instructions** — `docker-compose up` and it works
5. **Demo GIF or screenshot** — showing a real loan question being answered with clause citation
6. **Engineering decisions section** — explain WHY you chose clause-boundary chunking, WHY session scoping. This is what interviewers read.

---

## Resume Line

> "Built a private-document RAG system for loan agreement analysis with clause-boundary chunking and session-scoped vector stores — enabling plain-English Q&A over personal financial contracts with exact clause citations. Achieved 25% improvement in RAGAS faithfulness over naive chunking baseline."

*(Replace 25% with your actual number after running eval)*

---

## Interview Talking Points

**Q: Why clause-boundary chunking over standard chunking?**
> "Loan agreements are legally structured documents — each clause is a complete unit of meaning. Character-count chunking splits clauses mid-sentence, destroying the legal context. A chunk that contains half of clause 6.3 and half of clause 7.1 is useless for legal Q&A. Clause-boundary chunking ensures every retrieved chunk is a complete, citable legal statement."

**Q: Why session-scoped vector stores?**
> "In a multi-user system, you can't let one user's loan clauses pollute another's retrieval. Session scoping creates an isolated ChromaDB collection per user, cleared on session end. It's a basic data isolation requirement — the same reason you'd use separate DB rows per user."

**Q: What does RAGAS measure?**
> "Three things: Faithfulness — is the answer grounded in retrieved context or hallucinated? Context Precision — are the retrieved chunks actually relevant to the question? Answer Relevancy — does the answer address what was asked? I ran both naive and clause-chunked RAG on the same 15-question golden set to show the improvement isn't just claimed, it's measured."
