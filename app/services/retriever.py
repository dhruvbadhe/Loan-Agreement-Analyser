import chromadb
import os
from typing import List, Dict, Any
from app.core.config import settings
from app.services.embedder import embedder

os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

def get_collection(session_id: str):
    collection_name = f"loan_{session_id}"
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

def add_documents_to_session(session_id: str, chunks: List[Dict[str, Any]]):
    collection = get_collection(session_id)
    texts = [chunk["text"] for chunk in chunks]

    embeddings = embedder.embed_documents(texts)

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "clause_id": chunk["clause_id"],
            "page": chunk["page"],
            "char_offset": chunk["char_offset"]
        }
        for chunk in chunks
    ]
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

def query_session_collection(session_id: str, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    collection = get_collection(session_id)
    query_vector = embedder.embed_query(query_text)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
    )

    formatted_results = []
    if results and results["documents"] and len(results["documents"][0]) > 0:
        for i in range(len(results["documents"][0])):
            formatted_results.append({
                "text" : results["documents"][0][i],
                "clause_id" : results["metadatas"][0][i]["clause_id"],
                "page" : results["metadatas"][0][i]["page"],
                "distance" : results["distances"][0][i]
            })
    return formatted_results

def delete_session_collection(session_id: str):
    collection_name = f"loan_{session_id}"
    try:
        client.delete_collection(name=collection_name)
    except ValueError:
        pass 