from chromadb.utils import embedding_functions


class EmbeddingService:
    """
    Foloseste embedding-ul implicit al ChromaDB (ruleaza local, gratuit,
    fara nevoie de cheie API). Poate fi inlocuit ulterior cu OpenAI/Gemini
    embeddings daca vrei calitate mai buna.
    """

    def __init__(self):
        self.ef = embedding_functions.DefaultEmbeddingFunction()

    def embed(self, texts: list[str]):
        return self.ef(texts)


embedding_service = EmbeddingService()