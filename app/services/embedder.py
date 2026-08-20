import asyncio
import httpx
from typing import List
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings

class HuggingFaceEmbedder:
    def __init__(self):
        self.api_url = "https://router.huggingface.co/hf-inference/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
        self.headers = {}
        if settings.HF_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.HF_TOKEN}"
        self.executor = ThreadPoolExecutor(max_workers=1)

    async def _embed_batch_async(self, client: httpx.AsyncClient, batch: List[str]) -> List[List[float]]:
        response = await client.post(
            self.api_url,
            headers=self.headers,
            json={"inputs": batch},
            timeout=60.0
        )
        response.raise_for_status()
        return response.json()

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
            raise RuntimeError(f"Failed to generate embeddings from HuggingFace API: {e}")

    def embed_query(self, text: str) -> List[float]:
        embeddings = self.embed_documents([text])
        return embeddings[0] if embeddings else []

embedder = HuggingFaceEmbedder()
