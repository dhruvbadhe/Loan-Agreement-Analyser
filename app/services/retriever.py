import chromadb
import os
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from app.core.config import settings
from app.services.embedder import embedder
import re


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

def reciprocal_rank_fusion(
    dense_results: List[Dict[str, Any]], 
    sparse_results: List[Dict[str, Any]], 
    k: int = 60,
    dense_weight: float = 0.8,
    sparse_weight: float = 0.2
) -> List[Dict[str, Any]]:
    
    rrf_scores = {}
    doc_map = {}
    
    for rank, doc in enumerate(dense_results):
        doc_text = doc["text"]
        doc_map[doc_text] = doc
        rrf_scores[doc_text] = rrf_scores.get(doc_text, 0.0) + (dense_weight / (k + rank + 1))
        
    for rank, doc in enumerate(sparse_results):
        doc_text = doc["text"]
        doc_map[doc_text] = doc
        rrf_scores[doc_text] = rrf_scores.get(doc_text, 0.0) + (sparse_weight / (k + rank + 1))
        
    sorted_docs = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

    return [doc_map[doc] for doc in sorted_docs]


def tokenize(text: str) -> List[str]:
    return re.findall(r'\w+', text.lower())

def query_session_collection(session_id: str, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    collection = get_collection(session_id)
    
    db_data = collection.get()
    documents = db_data.get("documents", [])
    metadatas = db_data.get("metadatas", [])
    
    if not documents:
        return []
        
    tokenized_corpus = [tokenize(doc) for doc in documents]
    bm25 = BM25Okapi(tokenized_corpus)
    
    tokenized_query = tokenize(query_text)
    bm25_scores = bm25.get_scores(tokenized_query)
  
    sparse_results = []
    for idx, score in enumerate(bm25_scores):
        if score > 0.0:  # Only count actual matches
            sparse_results.append({
                "text": documents[idx],
                "clause_id": metadatas[idx]["clause_id"],
                "page": metadatas[idx]["page"],
                "score": score
            })
    sparse_results = sorted(sparse_results, key=lambda x: x["score"], reverse=True)
    
    query_vector = embedder.embed_query(query_text)
    vector_results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k * 2  # Retrieve more than top_k to allow better fusion
    )
    
    dense_results = []
    if vector_results and vector_results["documents"] and len(vector_results["documents"][0]) > 0:
        for i in range(len(vector_results["documents"][0])):
            dense_results.append({
                "text": vector_results["documents"][0][i],
                "clause_id": vector_results["metadatas"][0][i]["clause_id"],
                "page": vector_results["metadatas"][0][i]["page"]
            })
            
    unified_results = reciprocal_rank_fusion(dense_results, sparse_results)
    return sorted(unified_results, key=lambda x: x.get("score", 0.0) if "score" in x else 0.0, reverse=True)[:top_k]

def delete_session_collection(session_id: str):
    collection_name = f"loan_{session_id}"
    try:
        client.delete_collection(name=collection_name)
    except ValueError:
        pass