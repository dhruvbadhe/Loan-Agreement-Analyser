import uvicorn 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import ingest, query, session

app = FastAPI(title="Loan Agreement Analyser API", version="1.0.0", description="A session-scoped RAG API using local HuggingFace embeddings and Groq LLM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, tags=["Ingestion"])
app.include_router(query.router, tags=["Query"])
app.include_router(session.router, tags=["Session Management"])

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": "Loan Agreement Analyser API is running."}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)