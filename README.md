# Wavelength

Wavelength is a modern personal knowledge agent for semantically searching, summarizing, and questioning your saved documents and inspirations. It pairs a FastAPI backend with retrieval over Pinecone and grounded reasoning through the OpenAI Responses API.

## What Changed

- OpenAI Responses API replaces the legacy generation path.
- Structured outputs now power grounded answers, topic summaries, timeline reconstruction, and connection analysis.
- Retrieval quality improved with hybrid reranking that combines vector similarity and lexical overlap.
- Request IDs, JSON logging, retries, timeouts, and health checks make the backend more production-ready.
- Docker, `docker-compose`, and GitHub Actions make the project deployable on Railway, Render, or Fly.io.

## Architecture

The backend is organized around clear responsibilities:

- `backend/app/api`: FastAPI routes and HTTP concerns
- `backend/app/services`: AI orchestration and embedding workflows
- `backend/app/retrieval`: retrieval pipelines and reranking
- `backend/app/agents`: lightweight query routing
- `backend/app/schemas`: request and response contracts
- `backend/app/utils`: logging, request context, retries, and caching

## Local Development

### Backend

```bash
cd backend
cp .env.example .env
uv sync
UV_CACHE_DIR=/tmp/uv-cache uv run uvicorn main:app --reload
```

Backend runs on [http://localhost:8000](http://localhost:8000).

### Frontend

```bash
cd frontend
cp .env.example .env
pnpm install
pnpm dev
```

Frontend runs on [http://localhost:5173](http://localhost:5173).

### Docker

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

The API health endpoint is available at [http://localhost:8000/health](http://localhost:8000/health).

## Core APIs

- `GET /health`: service health and dependency readiness
- `GET /items/search`: hybrid semantic search over the knowledge base
- `POST /knowledge/ask`: grounded QA with citations and structured payloads
- `POST /knowledge/ask/stream`: streaming grounded answers
- `POST /knowledge/summaries`: topic summaries grounded in retrieved sources
- `POST /knowledge/timeline`: timeline reconstruction from source material
- `POST /knowledge/connections`: structured connection analysis across selected items

## Deployment

- Railway / Render: deploy `backend/` as a Python service using `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Fly.io: use `backend/Dockerfile`
- Static frontend hosting: build `frontend/` and serve `dist/`, or use `frontend/Dockerfile`

## Documentation

- [Backend README](./backend/README.md)
- [Frontend README](./frontend/README.md)
- [Design Notes](./DESIGN.md)

## License

MIT
