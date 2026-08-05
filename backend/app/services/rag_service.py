import uuid

import chromadb

from app.config import get_settings
from app.services.embedding_service import embedding_service

settings = get_settings()


class RAGService:
    """
    Aici e 'memoria comuna': indiferent ce model AI foloseste userul,
    toate conversatiile sunt salvate aici si cautate aici, deci
    orice model are acces la acelasi istoric.
    """

    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="memory",
            embedding_function=embedding_service.ef,
        )

    def add_memory(self, user_id: int, text: str, metadata: dict | None = None):
        meta = {"user_id": str(user_id)}
        if metadata:
            meta.update(metadata)
        doc_id = str(uuid.uuid4())
        self.collection.add(documents=[text], metadatas=[meta], ids=[doc_id])

    def get_chat_context(self, user_id: int, query: str, n_results: int = 4) -> str:
        try:
            count = self.collection.count()
            if count == 0:
                return ""
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, count),
                where={"user_id": str(user_id)},
            )
            docs = results.get("documents", [[]])[0]
            return "\n".join(docs)
        except Exception:
            # daca RAG-ul pica, chat-ul tot trebuie sa mearga, doar fara context
            return ""


rag_service = RAGService()