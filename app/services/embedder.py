from sentence_transformers import SentenceTransformer
from app.core.config import settings
from typing import List

class LocalEmbedder:

    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, show_progress_bar=True,)
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode(text, show_progress_bar=True,)
        return embedding.tolist()

embedder = LocalEmbedder()
