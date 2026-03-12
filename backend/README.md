# Backend

The backend is a FastAPI application organized around API routes, retrieval, and AI orchestration.

## Key Modules

- `main.py`: deployable ASGI entrypoint
- `app/api/routes`: HTTP routes for items, knowledge workflows, and health
- `app/services/knowledge.py`: OpenAI Responses orchestration with structured outputs
- `app/retrieval/pipeline.py`: semantic retrieval plus lightweight reranking
- `app/services/embeddings.py`: async embedding generation, Pinecone sync, and caching
- `app/utils`: request IDs, JSON logging, retries, and TTL caching

## Local Run

```bash
cp .env.example .env
uv sync
UV_CACHE_DIR=/tmp/uv-cache uv run uvicorn main:app --reload
```

## Environment Variables

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_EMBEDDING_MODEL`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `DATABASE_URL`
- `CORS_ORIGINS`
