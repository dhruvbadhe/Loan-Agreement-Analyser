import httpx
from typing import List
from app.core.config import settings

class HuggingFaceEmbedder:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
        self.headers = {}

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            response = httpx.post(
                self.api_url,
                headers=self.headers,
                json={"inputs": texts},
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings from HuggingFace API: {e}")

    def embed_query(self, text: str) -> List[float]:
        embeddings = self.embed_documents([text])
        return embeddings[0] if embeddings else []

embedder = HuggingFaceEmbedder()
