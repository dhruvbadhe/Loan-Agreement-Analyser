# Bug Log: NumPy 2.0 Compatibility Issue

## 1. AttributeError: `np.float_` was removed in the NumPy 2.0 release
- **Detected:** 2026-08-12
- **Symptoms:** Running the FastAPI backend throws an error during ChromaDB imports:
  ```python
  AttributeError: `np.float_` was removed in the NumPy 2.0 release. Use `np.float64` instead.
  ```
- **Root Cause:** ChromaDB version `0.4.24` uses `np.float_`, which was deprecated and removed in NumPy version `2.0.0`. When `sentence-transformers` or `torch` are installed, they pull in the latest NumPy 2.x version by default, causing ChromaDB to crash on import.
- **Resolution:** Pin `numpy<2.0.0` in `requirements.txt` to force pip to downgrade NumPy to a compatible 1.x version (such as `1.26.4`), or upgrade ChromaDB. Since version pinning is preferred, we enforce `numpy<2.0.0`.

## 2. ImportError: cannot import name 'HttpException' from 'fastapi'
- **Detected:** 2026-08-12
- **Symptoms:** Server startup fails with:
  ```python
  ImportError: cannot import name 'HttpException' from 'fastapi'
  ```
- **Root Cause:** Casing typo in `app/routers/query.py`. The standard exception class in FastAPI is capitalized as `HTTPException` (all uppercase HTTP), not `HttpException`.
- **Resolution:** Change `from fastapi import APIRouter, HttpException` to `from fastapi import APIRouter, HTTPException` in `app/routers/query.py`.

## 3. TypeError: __init__() got an unexpected keyword argument 'proxies'
- **Detected:** 2026-08-12
- **Symptoms:** Server startup fails inside `groq` initialization with:
  ```python
  TypeError: __init__() got an unexpected keyword argument 'proxies'
  ```
- **Root Cause:** Newer versions of `httpx` (version `0.28.0` and above) removed the deprecated `proxies` argument from client initializers. The `groq` SDK internally makes calls passing this argument to `httpx`.
- **Resolution:** Pin `httpx<0.28.0` in `requirements.txt` to downgrade `httpx` to a version (like `0.27.2`) that still supports the parameter.

## 4. Ingestion failed: cannot open broken document
- **Detected:** 2026-08-12
- **Symptoms:** Streamlit shows `Processing failed: {"detail":"Ingestion failed: cannot open broken document"}`.
- **Root Cause:** The downloaded `sample_loan.pdf` file is only 4.9KB. It contains HTML text of a 403 Forbidden page or redirect page returned by eForms' Cloudflare protection, rather than actual PDF bytes.
- **Resolution:** Download a clean PDF from a source that does not block curl (e.g., standard W3C dummy PDF or SEC files), or download via a web browser and upload the valid PDF file.

## 5. KeyError: 'page' when Ingesting
- **Detected:** 2026-08-12
- **Symptoms:** Server logs show `KeyError: 'page'` inside `retriever.py:add_documents_to_session` during parsing.
- **Root Cause:** A mismatch in dictionary keys between services. `chunker.py` outputs chunks with `"page_num"`, but `retriever.py` attempts to read `chunk["page"]`.
- **Resolution:** Align the keys by using `"page"` in `chunker.py` or `chunk["page_num"]` in `retriever.py`. We standardise on `"page"` in `chunker.py` and across metadata.

## 6. Malformed list comprehension for ids in retriever.py
- **Detected:** 2026-08-12
- **Symptoms:** ChromaDB insertion fails because of a length mismatch between IDs and documents.
- **Root Cause:** In `retriever.py` line 23, the list comprehension for `ids` is incorrectly wrapped inside a string literal: `ids = [f"chunk_{i} for i in range(len(chunks))]"]`. This results in a single string item inside the list instead of an array of IDs matching the length of `chunks`.
- **Resolution:** Change line 23 to `ids = [f"chunk_{i}" for i in range(len(chunks))]`.

## 7. NameError: name 'page' is not defined
- **Detected:** 2026-08-12
- **Symptoms:** Upload fails with `Processing failed: {"detail":"Ingestion failed: name 'page' is not defined"}`.
- **Root Cause:** In `chunker.py` lines 42 and 56, the code assigns `"page_num" : page`, but the variable defined above it on line 37 is named `page_num`. Because `page` is not defined as a variable, a NameError is thrown.
- **Resolution:** Change lines 42 and 56 to `"page": page_num`. This aligns the dictionary keys with retriever expectation and resolves the undefined variable reference.

## 8. Missing Return Statement in find_page_for_char
- **Detected:** 2026-08-12
- **Symptoms:** Ingestion fails with `Processing failed: {"detail":"Ingestion failed: Expected metadata value to be a str, int, float or bool, got None which is a <class 'NoneType'>"}`.
- **Root Cause:** In `pdf_parser.py`, the function `find_page_for_char` loops and updates `assigned_page`, but does not contain a `return assigned_page` statement at the end of the function scope. This results in Python implicitly returning `None`, which causes a metadata format validation crash when ChromaDB receives a `None` value.
- **Resolution:** Add `return assigned_page` at the end of the `find_page_for_char` function in `app/services/pdf_parser.py`.

## 9. 3D List Nesting of Query Embeddings in retriever.py Query
- **Detected:** 2026-08-12
- **Symptoms:** Query fails with `ValueError: Expected each value in the embedding to be a int or float, got [[[...]]]` (triple-nested brackets).
- **Root Cause:** In `embedder.py`, the `embed_query` function encodes `[text]` as a list: `self.model.encode([text])`. This returns a 2D array representing a batch of 1 document. Convert to list results in `[[values]]`. In `retriever.py`, the list is wrapped again: `query_embeddings=[query_vector]`, which translates to a 3D structure `[[[values]]]`.
- **Resolution:** Modify `embed_query` in `app/services/embedder.py` to encode the string `text` directly (without list brackets) so it returns a 1D array/list: `self.model.encode(text)`.







