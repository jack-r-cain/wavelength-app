# Wavelength

> Find what resonates

A personal influence archive powered by AI. Save albums, films, books, quotes, and places that inspire you. AI discovers patterns in your taste and recommends what to explore next.

## Screenshot

[Add a screenshot here later]

## Tech Stack

**Backend:**

- FastAPI + Python 3.13
- SQLModel (ORM)
- Anthropic Claude API
- Pinecone (Vector DB)

**Frontend:**

- React 19 + TypeScript
- Vite
- Tailwind CSS v4
- TanStack Query
- React Router

## Getting Started

**Prerequisites:**

- Python 3.13+
- Node.js 18+
- pnpm

**Backend:**

```bash
cd backend
uv sync
uv run fastapi dev app/main.py
```

Runs on http://localhost:8000

**Frontend:**

```bash
cd frontend
pnpm install
pnpm dev
```

Runs on http://localhost:5173

## Project Status

- [x] Module 0: Development setup
- [ ] Module 1: Database & CRUD API
- [ ] Module 2: Embeddings & Semantic Search
- [ ] Module 3: RAG & AI Connections
- [ ] Module 4: LangChain & Chat Interface

## Documentation

- [Backend README](./backend/README.md)
- [Frontend README](./frontend/README.md)

## License

MIT
