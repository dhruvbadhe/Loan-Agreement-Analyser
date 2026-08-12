from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.retriever import query_session_collection 
from app.services.generator import generate_answer

router = APIRouter()

class QueryRequest(BaseModel):
    session_id: str
    question: str

class Citation(BaseModel):
    clause_id: str
    page: int
    text: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]

@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    if not request.session_id.strip() or not request.question.strip():
        raise HTTPException(status_code=400, detail="Session ID and question must be provided.")

    try:
        retrieved_chunks = query_session_collection(request.session_id, request.question, top_k=5)

        answer = generate_answer(request.question, retrieved_chunks)

        citations = []

        for chunk in retrieved_chunks:
            citations.append(Citation(
                clause_id=chunk["clause_id"],
                page=chunk["page"],
                text=chunk["text"]
            ))

        return QueryResponse(answer=answer, citations=citations)
    except ValueError as val_err:
        raise HttpException(status_code=404, detail=f"Session not found or expired. Please upload the document again. Error: {str(val_err)} ")

    except Exception as e:
        raise HttpException(status_code=500, detail=f"Query Failed: {str(e)}")
    