import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.services.pdf_parser import parse_pdf
from app.services.chunker import chunk_by_clause
from app.services.retriever import add_documents_to_session

router = APIRouter()

class IngestResponse(BaseModel):
    session_id: str
    chunks_created: int
    clauses_found: int
    pages: int

@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    session_id = str(uuid.uuid4())[:8]

    temp_dir = "./temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{session_id}_{file.filename}")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        full_text, page_map = parse_pdf(temp_file_path)
        chunks = chunk_by_clause(full_text, page_map)

        if not chunks:
            raise HTTPException(status_code=400, detail="Unable to extract chunks from PDF.")

        add_documents_to_session(session_id, chunks)

        clauses_found = sum(1 for c in chunks if c["clause_id"]!= "General" and c['clause_id']!= "N/A")
        total_pages = len(set(page_map.values()))

        return IngestResponse(
            session_id=session_id,
            chunks_created=len(chunks),
            clauses_found=clauses_found,
            pages=total_pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)   
            
    