import chromadb

from src.db.chroma_client import collection_stats, get_collection


def test_collection_reachable():
    col = get_collection()
    assert isinstance(col, chromadb.Collection)


def test_collection_stats():
    stats = collection_stats()
    assert "document_count" in stats
    assert "collection_name" in stats
