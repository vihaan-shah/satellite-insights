"""
Chroma vector store for RAG over past situation briefs.
Uses sentence-transformers for local embeddings (no external API needed).
"""
import os
from typing import Optional

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

_collection = None


def init_vectorstore():
    """Initialize Chroma collection. Called on app startup."""
    global _collection
    try:
        import chromadb
        from chromadb.config import Settings

        client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        _collection = client.get_or_create_collection(
            name="situation_briefs",
            metadata={"hnsw:space": "cosine"},
        )
        print(f"[VectorStore] Chroma initialized at {CHROMA_PERSIST_DIR}")
    except Exception as exc:
        print(f"[VectorStore] Failed to initialize Chroma: {exc}")
        _collection = None


def store_brief(event_id: str, brief: str, metadata: Optional[dict] = None):
    """Embed and store a situation brief in Chroma."""
    if _collection is None:
        return
    try:
        _collection.upsert(
            ids=[event_id],
            documents=[brief],
            metadatas=[metadata or {}],
        )
    except Exception as exc:
        print(f"[VectorStore] Failed to store brief: {exc}")


class _Doc:
    """Minimal document object compatible with LangChain Document interface."""
    def __init__(self, page_content: str, metadata: dict):
        self.page_content = page_content
        self.metadata = metadata


def search_briefs(query: str, k: int = 3) -> list[_Doc]:
    """Semantic search over stored briefs. Returns top-k most similar docs."""
    if _collection is None:
        return []
    try:
        results = _collection.query(query_texts=[query], n_results=min(k, _collection.count()))
        docs = []
        for doc, meta in zip(
            results.get("documents", [[]])[0],
            results.get("metadatas", [[]])[0],
        ):
            docs.append(_Doc(page_content=doc, metadata=meta))
        return docs
    except Exception as exc:
        print(f"[VectorStore] Search failed: {exc}")
        return []
