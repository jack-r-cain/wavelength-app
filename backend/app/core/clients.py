from functools import lru_cache

import httpx
from openai import AsyncOpenAI
from pinecone import Pinecone

from app.core.config import settings


@lru_cache
def get_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=httpx.Timeout(settings.OPENAI_TIMEOUT_SECONDS),
        max_retries=settings.OPENAI_MAX_RETRIES,
    )


@lru_cache
def get_pinecone_index():
    client = Pinecone(api_key=settings.PINECONE_API_KEY)
    return client.Index(settings.PINECONE_INDEX_NAME)
