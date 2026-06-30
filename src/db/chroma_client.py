import chromadb
from chromadb import Collection

from src.config import config

_client: chromadb.PersistentClient | None = None
_collection: Collection | None = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=config.chroma_persist_dir)
    return _client


def get_collection() -> Collection:
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=config.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def collection_stats() -> dict:
    col = get_collection()
    return {
        "document_count": col.count(),
        "collection_name": col.name,
        "persist_dir": config.chroma_persist_dir,
    }


def reset_collection() -> None:
    """Delete and recreate the collection. FOR DEVELOPMENT ONLY."""
    global _collection
    client = _get_client()
    print(
        f"[WARNING] reset_collection() will permanently delete all documents "
        f"in '{config.chroma_collection_name}'. This is irreversible."
    )
    client.delete_collection(name=config.chroma_collection_name)
    _collection = None
    get_collection()
    print(f"[INFO] Collection '{config.chroma_collection_name}' recreated (empty).")
