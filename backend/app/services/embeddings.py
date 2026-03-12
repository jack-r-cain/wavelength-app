import asyncio
import hashlib
import logging

from app.core.clients import get_openai_client, get_pinecone_index
from app.core.config import settings
from app.utils.cache import TTLCache
from app.utils.retries import with_retries


logger = logging.getLogger(__name__)
embedding_cache = TTLCache[list[float]](ttl_seconds=900, max_size=512)


def create_text_for_embedding(item) -> str:
    parts = [item.title]
    if getattr(item, "creator", None):
        parts.append(f"by {item.creator}")
    parts.append(str(item.type))
    if getattr(item, "year", None):
        parts.append(f"from {item.year}")
    if getattr(item, "notes", None):
        parts.append(f"Notes: {item.notes}")
    return ". ".join(parts)


async def generate_embedding(text: str) -> list[float]:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    cache_key = hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()
    cached = embedding_cache.get(cache_key)
    if cached is not None:
        return cached

    client = get_openai_client()

    async def _create_embedding() -> list[float]:
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    embedding = await with_retries(_create_embedding)
    embedding_cache.set(cache_key, embedding)
    return embedding


async def store_item_embedding(item) -> None:
    if not settings.PINECONE_API_KEY:
        logger.warning("Skipping embedding upsert because Pinecone is not configured")
        return

    embedding = await generate_embedding(create_text_for_embedding(item))
    index = get_pinecone_index()

    def _upsert() -> None:
        index.upsert(
            vectors=[
                {
                    "id": str(item.id),
                    "values": embedding,
                    "metadata": {
                        "title": item.title,
                        "type": str(item.type),
                        "creator": item.creator,
                        "year": item.year,
                        "notes": item.notes,
                    },
                }
            ]
        )

    await with_retries(lambda: asyncio.to_thread(_upsert))


async def delete_item_embedding(item_id: int) -> None:
    if not settings.PINECONE_API_KEY:
        return

    index = get_pinecone_index()
    await with_retries(lambda: asyncio.to_thread(index.delete, ids=[str(item_id)]))


async def search_items(query: str, top_k: int = 10) -> list[dict]:
    if not settings.PINECONE_API_KEY:
        return []

    query_embedding = await generate_embedding(query)
    index = get_pinecone_index()

    def _query():
        return index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
        )

    results = await with_retries(lambda: asyncio.to_thread(_query))

    return [
        {
            "id": int(match.id),
            "score": float(match.score),
            "title": match.metadata.get("title"),
            "type": match.metadata.get("type"),
            "creator": match.metadata.get("creator"),
            "year": match.metadata.get("year"),
            "notes": match.metadata.get("notes"),
        }
        for match in results.matches  # type: ignore[attr-defined]
    ]
