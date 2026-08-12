from fastapi import APIRouter, HTTPException
from app.services.retriever import delete_session_collection

router = APIRouter()

@router.delete("/session/{session_id}")
async def end_session(session_id: str):
    if not session_id.strip():
        raise HTTPException(status_code=400, detail="Session ID cannot be empty.")

    try:
        delete_session_collection(session_id)
        return {"status": "success", "message": f"Session {session_id} vector store cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session:{str(e)}")

    