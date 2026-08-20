import asyncio
import httpx
from typing import List
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings

class GeminiEmbedder:
    def __init__(self):
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents"
        self.headers = {"Content-Type": "application/json"}
        self.executor = ThreadPoolExecutor(max_workers=1)

    async def _embed_batch_async(self, client: httpx.AsyncClient, batch: List[str]) -> List[List[float]]:
        requests_payload = []
        for text in batch:
            requests_payload.append({
                "model": "models/gemini-embedding-001",
                "content": {
                    "parts": [{"text": text}]
                }
            })
        
        url = f"{self.api_url}?key={settings.GEMINI_API_KEY}"
        response = await client.post(
            url,
            headers=self.headers,
            json={"requests": requests_payload},
            timeout=60.0
        )
        response.raise_for_status()
        
        data = response.json()
        embeddings = []
        for emb_obj in data.get("embeddings", []):
            embeddings.append(emb_obj.get("values", []))
        return embeddings

    async def _embed_all_async(self, texts: List[str]) -> List[List[float]]:
        batch_size = 16
        async with httpx.AsyncClient() as client:
            tasks = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                tasks.append(self._embed_batch_async(client, batch))
            results = await asyncio.gather(*tasks)
            
        all_embeddings = []
        for r in results:
            all_embeddings.extend(r)
        return all_embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        def _run():
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self._embed_all_async(texts))
            finally:
                loop.close()
                
        try:
            return self.executor.submit(_run).result()
        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings from Gemini API: {e}")

    def embed_query(self, text: str) -> List[float]:
        embeddings = self.embed_documents([text])
        return embeddings[0] if embeddings else []

embedder = GeminiEmbedder()
