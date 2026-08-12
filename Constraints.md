# System Constraints

The following rules define the boundaries and constraints of the codebase. These should never be altered or violated by AI edits:

## 1. Data Isolation & Security
- **No Shared Collections:** Under no circumstances should user collections in ChromaDB mix or fall back to a default global collection. Every request must be isolated by a validated, non-empty `session_id`.
- **No Permanent Contract Storage:** Extracted PDF files must be deleted immediately after ingestion and embedding. They must be cleaned up in a `finally` block to guarantee removal even on ingestion failures.

## 2. API Synchronicity & Timeouts
- **No Sync Evaluation:** The `/eval` endpoint must run asynchronously. RAGAS evaluation involves multiple sequential LLM calls which exceed standard HTTP timeout limits (e.g., 30s).
- **Rate Limits:** LLM and embedding API calls must have explicit token rate limit controls and exponential backoffs to prevent service disruption.

## 3. Error Mapping
- **No Silent DB Failures:** Database lookup failures on missing or reaped session collections must raise HTTP 404 Exceptions. Unhandled 500 errors must be avoided to keep clients properly informed of session state.

## 4. Dependency Pinning
- **No Floating Versions:** All third-party libraries (e.g., `chromadb`, `pymupdf`, `ragas`, `fastapi`, `openai`) must be strictly pinned in dependencies to avoid breaking changes.

