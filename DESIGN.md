# Wavelength — Technical Design Document

> Personal influence archive with AI-powered semantic search and taste analysis.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Backend Components](#3-backend-components)
4. [Frontend Components](#4-frontend-components)
5. [Data Models](#5-data-models)
6. [Key Workflows](#6-key-workflows)
7. [Technical Decisions](#7-technical-decisions)
8. [Performance Characteristics](#8-performance-characteristics)
9. [Development Environment](#9-development-environment)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Security Considerations](#11-security-considerations)
12. [Implementation Checklist](#12-implementation-checklist)
13. [Known Limitations & Future Work](#13-known-limitations--future-work)
14. [API Reference](#14-api-reference)
15. [Error Handling](#15-error-handling)
16. [Monitoring & Observability](#16-monitoring--observability)

---

## 1. Project Overview

Wavelength is a personal archive for tracking cultural influences — albums, films, books, people, and places. It layers AI on top of a simple CRUD store to enable three capabilities:

- **Semantic search** — find items by meaning, not just keyword, using vector embeddings
- **Taste analysis chat** — ask questions about your collection and get context-aware answers with streaming responses
- **Connection finding** — select multiple items and have an LLM identify the threads connecting them

The system consists of a Python/FastAPI backend and a React/TypeScript frontend. All AI capabilities are provided by external services (OpenAI for embeddings, Anthropic Claude for generation, Pinecone for vector storage).

---

## 2. System Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Browser                          │
│                                                     │
│  React 19 + TypeScript + Vite                       │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ TanStack │  │    Zustand   │  │  use-debounce │  │
│  │  Query   │  │  (UI state)  │  │  (search)     │  │
│  └──────────┘  └──────────────┘  └───────────────┘  │
│        │              │                 │            │
│        └──────── axios / fetch ─────────┘            │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP / SSE
                      │ localhost:8000
┌─────────────────────▼───────────────────────────────┐
│                  FastAPI (uvicorn)                   │
│                                                     │
│  app/main.py — CORS, lifespan, router mount         │
│  app/api/routes/items.py — 9 endpoints              │
│  app/core/config.py — Pydantic Settings             │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │              Services Layer                   │   │
│  │  embeddings.py   rag.py   conversation.py    │   │
│  └──────────────────────────────────────────────┘   │
│                    │                                 │
│  SQLite (wavelength.db)   ← SQLModel ORM            │
└──────────┬───────────────────────────────────────────┘
           │
           ├── OpenAI API (text-embedding-3-small)
           ├── Pinecone (wavelength-dev index)
           ├── Anthropic API (claude-sonnet-4-20250514)
           └── LangSmith (tracing, optional)
```

### Directory Structure

```
wavelength-app/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app, CORS, lifespan
│   │   ├── database.py              # SQLite engine, session dependency
│   │   ├── models.py                # Item SQLModel table
│   │   ├── schemas.py               # ItemCreate / ItemUpdate / ItemResponse
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── items.py         # All 9 REST endpoints
│   │   ├── core/
│   │   │   └── config.py            # Pydantic Settings (env vars)
│   │   └── services/
│   │       ├── embeddings.py        # OpenAI + Pinecone integration
│   │       ├── rag.py               # LangChain chains (connections + chat)
│   │       └── conversation.py      # In-memory chat history store
│   ├── pyproject.toml
│   └── .env                         # API keys (gitignored)
│
└── frontend/
    └── src/
        ├── main.tsx                 # React root, QueryClientProvider
        ├── App.tsx                  # Shell: header, tabs, add-item modal
        ├── api/
        │   └── items.ts             # itemsApi object (axios wrappers)
        ├── components/
        │   ├── AddItemForm.tsx
        │   ├── EditItemForm.tsx
        │   ├── ChatInterface.tsx
        │   ├── FindConnections.tsx
        │   ├── ItemCard.tsx
        │   ├── ItemList.tsx
        │   ├── Modal.tsx
        │   ├── Searchbar.tsx
        │   └── Tabs.tsx
        ├── hooks/
        │   ├── useItems.ts          # TanStack Query hooks
        │   └── useStreamingChat.ts  # SSE streaming hook
        ├── lib/
        │   ├── api.ts               # axios instance (VITE_API_URL)
        │   └── queryClient.ts       # QueryClient singleton
        ├── stores/
        │   └── uiStore.ts           # Zustand UI state
        └── types/
            └── item.ts              # Item, ItemCreate, ItemUpdate, ItemWithScore
```

### Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Backend framework | FastAPI | ≥ 0.128 |
| ORM | SQLModel | ≥ 0.0.31 |
| Database | SQLite | (file: `wavelength.db`) |
| Embeddings | OpenAI `text-embedding-3-small` | — |
| Vector store | Pinecone (index: `wavelength-dev`) | ≥ 8.0 |
| LLM | Anthropic `claude-sonnet-4-20250514` | via LangChain |
| LLM framework | LangChain + LangChain-Anthropic | ≥ 0.3 |
| Config | Pydantic Settings | ≥ 2.12 |
| Python | 3.13 | (uv managed) |
| Frontend framework | React | 19 |
| Language | TypeScript | ~5.9 |
| Build tool | Vite | 7 |
| Server state | TanStack Query | v5 |
| Client state | Zustand | latest |
| HTTP client | axios | ≥ 1.13 |
| Styling | Tailwind CSS | v4 |
| Debounce | use-debounce | latest |

---

## 3. Backend Components

### 3.1 `app/main.py` — Application Entry Point

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()   # Creates SQLite schema on startup
    yield
    # shutdown: nothing to clean up

app = FastAPI(title="Wavelength API", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items.router)
```

**Key points:**
- Uses FastAPI's `lifespan` context manager (modern replacement for `@app.on_event`)
- CORS is locked to the Vite dev server origin (`localhost:5173`)
- A single router is mounted with no prefix (the router itself uses `/items`)
- Two utility endpoints: `GET /` and `GET /health`

---

### 3.2 `app/core/config.py` — Configuration

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./wavelength.db"
    OPENAI_API_KEY: str
    PINECONE_API_KEY: str
    ANTHROPIC_API_KEY: str
    LANGCHAIN_API_KEY: str
    SECRET_KEY: str = "dev-secret-key-replace-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()
```

**Key points:**
- `extra="ignore"` is required because `.env` contains `LANGCHAIN_TRACING_V2` and `LANGCHAIN_PROJECT` that aren't declared fields; without this, Pydantic raises a validation error at startup
- Pydantic Settings reads `.env` into the `settings` object but does **not** write to `os.environ` — any third-party client (e.g. LangChain's `ChatAnthropic`) that reads from `os.environ` must receive `api_key` explicitly
- `SECRET_KEY` and `ALGORITHM` are JWT placeholders; authentication is not yet implemented
- The module-level `settings = Settings()` instance is imported wherever config is needed

---

### 3.3 `app/database.py` — Database Layer

```python
DATABASE_URL = "sqlite:///./wavelength.db"

engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False}
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

**Key points:**
- `check_same_thread=False` is required for SQLite when FastAPI's thread pool runs sync routes across threads
- `echo=True` logs every SQL statement to stdout — useful for development, should be disabled in production
- `get_session` is a FastAPI dependency (generator with `yield`) — the `with` block ensures the session is closed after each request, whether it succeeds or raises
- `DATABASE_URL` is currently hardcoded here rather than reading from `settings` — a minor inconsistency (both point to the same SQLite file)

---

### 3.4 `app/api/routes/items.py` — All Endpoints

Nine endpoints, with deliberate `def` vs `async def` choices:

```
POST   /items/              async  — BackgroundTasks (embedding after save)
POST   /items/connections   def    — blocking LangChain call → thread pool
POST   /items/ask           def    — blocking LangChain call → thread pool
POST   /items/ask/stream    async  — SSE async generator
GET    /items/              def    — SQLite → thread pool
GET    /items/search        def    — blocking OpenAI + Pinecone → thread pool
GET    /items/{id}          def    — SQLite → thread pool
PUT    /items/{id}          async  — BackgroundTasks (re-embed on change)
DELETE /items/{id}          def    — SQLite → thread pool
```

**The `def` vs `async def` rule applied here:**
FastAPI runs `def` endpoints in a thread pool executor, keeping the event loop free. `async def` runs directly on the event loop — correct for async I/O, but harmful for synchronous blocking calls (OpenAI SDK, Pinecone SDK, LangChain). Only endpoints that need `BackgroundTasks` injection or return async generators must be `async def`.

#### `POST /items/` — Create with Background Embedding

```python
@router.post("/", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    db_item = Item.model_validate(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    item_snapshot = db_item.model_copy()
    background_tasks.add_task(store_item_embedding, item_snapshot)

    return db_item
```

`model_copy()` creates a plain Pydantic snapshot before the session closes. After the response is sent, FastAPI tears down the session dependency — if the background task held a reference to the live ORM object, accessing lazy-loaded relationships would raise `DetachedInstanceError`. Since `Item` has no relationships (only scalar fields), passing `db_item` directly would also work, but `model_copy()` makes the intent explicit.

#### `PUT /items/{id}` — Selective Re-embedding

```python
_EMBEDDING_FIELDS = {"title", "creator", "year", "notes", "type"}

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(item_id, item_update, background_tasks, session):
    # ...apply changes, stamp updated_at...
    if update_data.keys() & _EMBEDDING_FIELDS:
        background_tasks.add_task(store_item_embedding, db_item.model_copy())
    return db_item
```

Re-embedding is only triggered if the update touches fields that contribute to the embedding text (`title`, `creator`, `year`, `notes`, `type`). Updating only `image_url` skips re-embedding.

#### `POST /items/ask/stream` — Server-Sent Events

```python
@router.post("/ask/stream")
async def ask_stream_endpoint(request, session):
    async def generate():
        try:
            for chunk in ask_about_taste_stream(
                request.question, session, request.session_id
            ):
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0)
        except Exception as e:
            yield f"data: [Error: {type(e).__name__} — {e}]\n\n"

    return StreamingResponse(generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
```

`await asyncio.sleep(0)` between chunks yields control back to the event loop, allowing the SSE bytes to be flushed to the client immediately rather than buffered. The try/except catches API errors (e.g. Anthropic 529 overloaded) and sends them as a readable error message instead of crashing the ASGI connection.

---

### 3.5 `app/services/embeddings.py` — Vector Operations

```python
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pinecone_client.Index("wavelength-dev")
```

**`create_text_for_embedding(item) -> str`**

Constructs the string that gets embedded. For an item like *Blood on the Tracks* by Bob Dylan (album, 1975) with notes "raw heartbreak":

```
"Blood on the Tracks. by Bob Dylan. album. from 1975. Notes: raw heartbreak"
```

Fields used (in order): `title`, `creator`, `type`, `year`, `notes`. `image_url` is excluded.

**`store_item_embedding(item)`**

1. Calls `create_text_for_embedding` to build the text string
2. Calls OpenAI `text-embedding-3-small` → 1536-dimensional float vector
3. Upserts to Pinecone with metadata `{title, type, creator, year}`

Pinecone vector ID is `str(item.id)` — the SQLite integer primary key serialized as a string.

**`search_items(query, top_k) -> list[dict]`**

1. Embeds the query string using `text-embedding-3-small`
2. Queries Pinecone for `top_k` nearest neighbors (cosine similarity)
3. Returns list of `{id, score, title, type, creator, year}` dicts

The `search` endpoint then hydrates these results by fetching the full `Item` from SQLite using each returned ID.

---

### 3.6 `app/services/rag.py` — LangChain Chains

All three functions use LangChain Expression Language (LCEL) with the `|` pipe operator.

**`find_connections(item_ids, session) -> str`**

```python
chain = prompt | llm | output_parser
response = chain.invoke({"context": context})
```

Single-turn, no history. Fetches requested items from SQLite, formats them with `build_context_from_items`, passes to Claude with a structured prompt asking for themes, patterns, and cross-item connections.

**`ask_about_taste(question, session, session_id) -> dict`**

```python
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_conversation,          # history getter by session_id
    input_messages_key='question',
    history_messages_key='history'
)
response = chain_with_history.invoke({...},
    config={'configurable': {'session_id': session_id}})
return {'answer': response, 'sources': [item.model_dump() for item in items]}
```

Multi-turn with conversation memory. Uses `MessagesPlaceholder` in the prompt template to inject prior messages. Returns both the answer and the source items used as context.

**`ask_about_taste_stream(question, session, session_id)` — generator**

Identical setup to `ask_about_taste` but uses `.stream()` instead of `.invoke()`:

```python
for chunk in chain_with_history.stream({...}, config={...}):
    yield chunk
```

Yields string tokens as they arrive from the Anthropic API. Consumed by the `ask_stream_endpoint` async generator.

**`build_context_from_items(items) -> str`**

Formats items into a numbered list for the LLM prompt:

```
1. Blood on the Tracks by Bob Dylan (album, 1975)
        Notes: raw heartbreak album

2. No Country for Old Men by Cormac McCarthy (book, 2005)
        Notes: nihilistic, sparse prose
```

**Important:** `ChatAnthropic` is instantiated with `api_key=settings.ANTHROPIC_API_KEY` explicitly. Without this, LangChain reads from `os.environ["ANTHROPIC_API_KEY"]` — but Pydantic Settings does not write to `os.environ`, only to the `settings` object.

---

### 3.7 `app/services/conversation.py` — Chat History

```python
conversations: dict[str, InMemoryChatMessageHistory] = {}

def get_conversation(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in conversations:
        conversations[session_id] = InMemoryChatMessageHistory()
    return conversations[session_id]
```

A module-level dict keyed by `session_id`. `RunnableWithMessageHistory` calls `get_conversation` before each chain invocation to retrieve (or create) the history for that session.

**Limitation:** In-memory only. History is lost on server restart. New chat sessions on the frontend use `crypto.randomUUID()` as their session ID.

---

## 4. Frontend Components

### 4.1 Entry Point — `src/main.tsx`

```tsx
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>
)
```

`QueryClientProvider` wraps the entire tree. Zustand store (`uiStore`) is self-contained and needs no provider.

---

### 4.2 `src/App.tsx` — Shell

Reads from Zustand for tab and modal state:

```tsx
const activeTab = useUIStore((state) => state.activeTab)
const setActiveTab = useUIStore((state) => state.setActiveTab)
const isModalOpen = useUIStore((state) => state.isModalOpen)
const openModal = useUIStore((state) => state.openModal)
const closeModal = useUIStore((state) => state.closeModal)
```

Renders a sticky header, the `<Tabs>` component with three tabs, and a `<Modal>` containing `<AddItemForm>`. Each tab's `content` is a JSX node defined inline in the `tabs` array.

---

### 4.3 `src/stores/uiStore.ts` — Zustand State

```typescript
type ActiveTab = 'collection' | 'chat' | 'insights'

interface UIState {
  activeTab: ActiveTab
  isModalOpen: boolean
  selectedItemIds: number[]       // used by FindConnections

  setActiveTab: (tab: ActiveTab) => void
  openModal: () => void
  closeModal: () => void
  toggleSelection: (id: number) => void
  clearSelection: () => void
}
```

`selectedItemIds` is shared state between `App` (which renders `FindConnections`) and `FindConnections` itself, allowing the selection to persist if a user switches tabs and comes back.

**State ownership:** `isEditing` in `ItemCard` stays local `useState` — it's per-card and unshared. `result` and `loading` in `FindConnections` stay local — they're not needed outside that component.

---

### 4.4 `src/api/items.ts` — API Layer

```typescript
export const itemsApi = {
  getAll: async (): Promise<Item[]>
  create: async (item: ItemCreate): Promise<Item>
  update: async (id: number, update: ItemUpdate): Promise<Item>
  delete: async (id: number): Promise<void>
  search: async (query: string, limit?: number): Promise<ItemWithScore[]>
}
```

All methods use the shared `api` axios instance from `src/lib/api.ts`:

```typescript
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})
```

`VITE_API_URL` is set in `frontend/.env` to `http://localhost:8000`.

---

### 4.5 `src/hooks/useItems.ts` — TanStack Query Hooks

```typescript
export function useItems()          // GET /items/ — ['items']
export function useCreateItem()     // POST /items/ — invalidates ['items']
export function useUpdateItem()     // PUT /items/{id} — invalidates ['items']
export function useDeleteItem()     // DELETE /items/{id} — invalidates ['items']
export function useSearchItems(query, limit)  // GET /items/search — ['items', 'search', query, limit]
```

All mutations use `queryClient.invalidateQueries({ queryKey: ['items'] })` on success, triggering a refetch of the list.

`useSearchItems` has `enabled: query.length > 0` to suppress requests when the search box is empty.

---

### 4.6 `src/hooks/useStreamingChat.ts` — SSE Hook

Manages the full streaming lifecycle:

```typescript
export function useStreamingChat(sessionId: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  // ...
  return { messages, sendMessage, isStreaming }
}
```

**Send flow:**
1. Appends user message to `messages`
2. POSTs to `/items/ask/stream` using native `fetch` (not axios — SSE requires a readable stream body, which axios doesn't expose as cleanly)
3. Gets a `ReadableStream` from `response.body`
4. Appends an empty assistant message as a placeholder
5. Reads chunks via `reader.read()`, parses `data: ` lines from the SSE format
6. Updates the last message in state on every 3rd chunk (batching to reduce React re-renders)
7. Does a final state update after the stream closes to ensure completeness

**Session management:** `sessionId` is initialized with `crypto.randomUUID()` and passed to each request. "New Chat" button generates a fresh UUID, creating a new conversation in the backend's `conversations` dict.

---

### 4.7 Component Reference

| Component | File | State | Purpose |
|---|---|---|---|
| `ChatInterface` | `components/ChatInterface.tsx` | local: `sessionId`, `input` | Renders message list, input form; uses `useStreamingChat` |
| `FindConnections` | `components/FindConnections.tsx` | Zustand: `selectedItemIds`; local: `result`, `loading` | Checkbox list, submits to `/items/connections` |
| `ItemCard` | `components/ItemCard.tsx` | local: `isEditing` | Card display with Edit/Delete; owns its edit modal |
| `ItemList` | `components/ItemList.tsx` | none | Grid of `ItemCard` via `useItems` |
| `Searchbar` | `components/Searchbar.tsx` | local: `searchQuery`, debounced | Search input → `useSearchItems` → grid of `ItemCard` |
| `AddItemForm` | `components/AddItemForm.tsx` | local: `formData` | Create form, uses `useCreateItem` |
| `EditItemForm` | `components/EditItemForm.tsx` | local: `formData` (pre-filled) | Edit form, uses `useUpdateItem` |
| `Modal` | `components/Modal.tsx` | none | Portal-style overlay with backdrop click-to-close |
| `Tabs` | `components/Tabs.tsx` | none (activeTab from parent) | Tab buttons + content render |

---

## 5. Data Models

### 5.1 SQLite Schema — `Item` table

Defined in `app/models.py`:

```python
class ItemType(str, Enum):
    ALBUM  = "album"
    FILM   = "film"
    BOOK   = "book"
    PERSON = "person"
    PLACE  = "place"

class Item(SQLModel, table=True):
    id:         int | None  = Field(default=None, primary_key=True)
    title:      str         = Field(index=True)
    type:       ItemType
    creator:    str | None  = Field(default=None, index=True)
    year:       int | None  = Field(default=None, ge=1700, le=2100)
    notes:      str | None  = None
    image_url:  str | None  = None
    created_at: datetime    = Field(default_factory=datetime.now)
    updated_at: datetime    = Field(default_factory=datetime.now)
```

Indexes on `title` and `creator` for SQL filtering. `year` is validated to the range 1700–2100 at the Pydantic level. `updated_at` is stamped manually in the `update_item` route handler (no ORM trigger).

### 5.2 API Schemas (`app/schemas.py`)

```python
class ItemBase(SQLModel):           # title, type, creator, year, notes, image_url
class ItemCreate(ItemBase): pass    # identical to base — all required except optionals
class ItemUpdate(SQLModel):         # all fields Optional — PATCH semantics
class ItemResponse(ItemBase):       # adds id, created_at, updated_at
```

`ItemUpdate` uses `model_dump(exclude_unset=True)` in the route so only fields actually provided in the request body are applied — true partial update.

### 5.3 TypeScript Types (`src/types/item.ts`)

```typescript
export const ItemType = {
  ALBUM: 'album', FILM: 'film', BOOK: 'book',
  PERSON: 'person', PLACE: 'place'
} as const
export type ItemType = (typeof ItemType)[keyof typeof ItemType]

export interface Item {
  id: number; title: string; type: ItemType
  creator: string | null; year: number | null
  notes: string | null; image_url: string | null
  created_at: string; updated_at: string
}
export interface ItemCreate {
  title: string; type: ItemType
  creator: string | null; year: number | null
  notes: string | null; image_url: string | null
}
export interface ItemUpdate {         // all optional — matches backend
  title?: string; type?: ItemType
  creator?: string | null; year?: number | null
  notes?: string | null; image_url?: string | null
}
export interface ItemWithScore extends Item { score: number }
```

### 5.4 Pinecone Vector Record

```json
{
  "id": "42",
  "values": [0.023, -0.18, ...],
  "metadata": {
    "title": "Blood on the Tracks",
    "type": "album",
    "creator": "Bob Dylan",
    "year": 1975
  }
}
```

- Vector ID is the SQLite integer PK serialized as a string
- Embedding model: `text-embedding-3-small` (1536 dimensions)
- Metadata is cached in Pinecone for display in search results (avoids a SQLite lookup per match, though the route currently does the lookup anyway for full item data)

---

## 6. Key Workflows

### 6.1 Adding an Item

```
User fills AddItemForm → clicks Submit
  │
  ▼
useCreateItem.mutate(formData)
  │  POST /items/  {title, type, creator, year, notes, image_url}
  ▼
create_item() [async]
  ├─ Item.model_validate(item)      — Pydantic → SQLModel
  ├─ session.add() → commit()       — write to SQLite
  ├─ session.refresh()              — get generated id
  ├─ db_item.model_copy()           — detached snapshot
  ├─ background_tasks.add_task(store_item_embedding, snapshot)
  └─ return ItemResponse            — HTTP 200 immediately
        │
        ▼ (after response sent)
        store_item_embedding(snapshot)
          ├─ create_text_for_embedding()   — build text string
          ├─ OpenAI embeddings.create()    — ~200ms
          └─ pinecone.index.upsert()       — ~100ms

Client receives 200
  └─ queryClient.invalidateQueries(['items'])
       └─ GET /items/ refetch → UI updates
```

### 6.2 Semantic Search

```
User types in Searchbar
  │  (300ms debounce via use-debounce)
  ▼
useSearchItems(debouncedQuery)
  │  GET /items/search?query=...
  ▼
search_items_endpoint() [def → thread pool]
  ├─ search_items(query, top_k=10)
  │    ├─ generate_embedding(query)    — OpenAI API
  │    └─ index.query(vector, top_k)  — Pinecone cosine similarity
  │         returns [{id, score, title, type, creator, year}, ...]
  └─ for each match:
       item = session.get(Item, match["id"])  — SQLite lookup
       return {...item.model_dump(), "score": match["score"]}

Client renders ItemCard grid with score badges
```

### 6.3 Streaming Chat

```
User types question → hits Send
  │
  ▼
useStreamingChat.sendMessage(question)
  ├─ append user message to local state
  ├─ setIsStreaming(true)
  ├─ fetch POST /items/ask/stream  {question, session_id}
  │
  ▼
ask_stream_endpoint() [async]
  └─ StreamingResponse(generate(), media_type="text/event-stream")

        generate() [async generator]
          └─ for chunk in ask_about_taste_stream():
               yield f"data: {chunk}\n\n"
               await asyncio.sleep(0)   ← flush to client

               ask_about_taste_stream() [sync generator]
                 ├─ search_items(question, top_k=5)   — find relevant items
                 ├─ build_context_from_items(items)   — format for prompt
                 ├─ ChatPromptTemplate + MessagesPlaceholder
                 ├─ ChatAnthropic(claude-sonnet-4-20250514)
                 └─ chain_with_history.stream()
                      yields token strings as Anthropic streams them

Client: ReadableStream reader
  ├─ parse "data: {chunk}" lines
  ├─ accumulate into assistantMessage
  ├─ update last message in state every 3 chunks (render batching)
  └─ final state update on stream close
```

### 6.4 Finding Connections

```
User selects items via checkboxes (Zustand selectedItemIds)
  │  (minimum 2 required)
  ▼
FindConnections.handleSubmit()
  │  POST /items/connections  {item_ids: [1, 3, 7]}
  ▼
find_connections_endpoint() [def → thread pool]
  └─ find_connections(item_ids, session)
       ├─ session.get(Item, id) for each id
       ├─ build_context_from_items(valid_items)
       ├─ ChatPromptTemplate (themes/patterns/why prompt)
       ├─ ChatAnthropic (single-turn, no history)
       └─ chain.invoke({"context": context})
            returns string

Client receives {explanation: "..."}
  └─ clearSelection() — reset Zustand selectedItemIds
  └─ render result panel
```

### 6.5 Editing an Item

```
User clicks Edit on ItemCard
  └─ isEditing = true  (local useState)
  └─ Modal opens with EditItemForm(item=item)

EditItemForm initialized with:
  formData = {title, type, creator, year, notes, image_url}
  (all pre-filled from item prop)

User changes fields → clicks Save Changes
  │
  ▼
useUpdateItem.mutate({id: item.id, update: formData})
  │  PUT /items/{id}  {only changed fields}
  ▼
update_item() [async]
  ├─ item_update.model_dump(exclude_unset=True)
  ├─ setattr(db_item, key, value) for each changed field
  ├─ db_item.updated_at = datetime.now()
  ├─ session.commit()
  ├─ if _EMBEDDING_FIELDS ∩ changed_fields:
  │    background_tasks.add_task(store_item_embedding, snapshot)
  └─ return updated ItemResponse

Client:
  └─ onSuccess → queryClient.invalidateQueries(['items'])
  └─ onSuccess → setIsEditing(false) → Modal closes
```

---

## 7. Technical Decisions

### 7.1 `def` vs `async def` for Route Handlers

FastAPI handles these differently:
- `def` → runs in a **thread pool executor** (via `anyio`), freeing the event loop
- `async def` → runs **directly on the event loop** — correct for native async I/O, but harmful for blocking sync calls

All service functions (`find_connections`, `ask_about_taste`, `search_items`, `store_item_embedding`) use synchronous SDKs. Running them inside `async def` routes would block the event loop for the duration of the OpenAI/Anthropic/Pinecone call (200ms–5s).

Only `create_item`, `update_item`, and `ask_stream_endpoint` are `async def`, because they inject `BackgroundTasks` or return async generators — both require the async context.

### 7.2 Embedding in Background Tasks

Instead of blocking the `POST /items/` response while waiting for OpenAI (~200ms) and Pinecone (~100ms), the embedding is deferred to a FastAPI `BackgroundTask`. The HTTP response returns immediately after the SQLite write. The tradeoff: a newly created item is searchable after a short delay (~300ms), not instantly.

`model_copy()` is used to snapshot the ORM object before the session dependency closes. This avoids `DetachedInstanceError` if SQLAlchemy ever lazy-loads a relationship in the background thread.

### 7.3 Pydantic Settings + `extra="ignore"`

Using Pydantic Settings centralizes all env var access and validates at startup (missing required keys fail immediately rather than at first use). `extra="ignore"` is necessary because the `.env` file contains LangSmith variables (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_PROJECT`, `LANGCHAIN_API_KEY`) that need to stay in the environment for LangChain to pick up, but aren't typed as `Settings` fields.

**Gotcha:** Pydantic Settings reads `.env` into Python object attributes but does NOT propagate to `os.environ`. Any library that reads `os.environ` directly (like LangChain's internal `ChatAnthropic` initialization) requires the key passed explicitly: `ChatAnthropic(api_key=settings.ANTHROPIC_API_KEY)`.

### 7.4 LangChain for LLM Orchestration

LangChain's `RunnableWithMessageHistory` handles conversation memory transparently — the route handler doesn't need to manually load/append history. The LCEL `|` pipe syntax makes chains readable: `prompt | llm | output_parser`.

Downside: LangChain adds abstraction overhead and has a known bug where error handling during streaming tries to read an unread httpx streaming response body, raising `httpx.ResponseNotRead` instead of the original API error. This is worked around with a `try/except` in the `generate()` async generator.

### 7.5 In-Memory Conversation History

`conversation.py` uses a module-level dict. This is simple and fast but has two limitations:
1. History is lost on server restart
2. No cleanup mechanism — long-running servers accumulate sessions indefinitely

For a personal single-user app this is acceptable. A production upgrade would use Redis or a database-backed store.

### 7.6 SSE over WebSockets

The streaming chat uses Server-Sent Events (SSE) rather than WebSockets. SSE is appropriate here because:
- Communication is strictly server → client (no client-initiated messages mid-stream)
- SSE works over standard HTTP, simpler to implement and debug
- The frontend uses native `fetch` + `ReadableStream` rather than axios, since SSE needs direct stream access

### 7.7 Zustand for Shared UI State

Local `useState` is used for per-component state (`isEditing` in `ItemCard`, `result`/`loading` in `FindConnections`). Zustand manages state that needs to be shared across the component tree without prop-drilling: `activeTab`, `isModalOpen`, and `selectedItemIds` (the last one matters because `FindConnections` is deep inside the `insights` tab content while the data it needs could theoretically be triggered from elsewhere).

### 7.8 TanStack Query Cache Invalidation Strategy

All mutations (`create`, `update`, `delete`) invalidate the `['items']` query key, triggering a full refetch of the item list. This is simple and correct. A more optimistic approach would update the cache directly (avoiding the refetch round-trip), but the current volume doesn't warrant the added complexity.

---

## 8. Performance Characteristics

### 8.1 Endpoint Latency Profile

| Endpoint | Bottleneck | Typical Latency |
|---|---|---|
| `GET /items/` | SQLite read | < 10ms |
| `GET /items/{id}` | SQLite read | < 5ms |
| `DELETE /items/{id}` | SQLite write | < 10ms |
| `POST /items/` (response) | SQLite write | < 20ms |
| `POST /items/` (embedding, background) | OpenAI + Pinecone | ~300ms |
| `GET /items/search` | OpenAI embedding + Pinecone query | ~400–600ms |
| `POST /items/connections` | Claude inference | ~2–5s |
| `POST /items/ask` (non-streaming) | OpenAI embed + Claude | ~3–6s |
| `POST /items/ask/stream` (first token) | OpenAI embed + Claude TTFT | ~1–2s |

### 8.2 Search Latency Breakdown

```
GET /items/search:
  generate_embedding(query)  ~200–400ms   (OpenAI API round-trip)
  index.query()              ~50–100ms    (Pinecone query)
  session.get() × N          ~1–5ms       (SQLite, N ≤ 10)
  Total:                     ~300–500ms
```

The 300ms debounce in `Searchbar` means searches fire at most every 300ms of inactivity. Combined with TanStack Query's cache, repeated identical queries hit the cache instead of the network.

### 8.3 Streaming UX Optimizations

The `useStreamingChat` hook batches React state updates to every 3 chunks rather than every chunk:

```typescript
if (updateCounter % 3 === 0 || done) {
  setMessages(...)
  await new Promise(resolve => setTimeout(resolve, 10))
}
```

This reduces the number of React re-renders during a stream from ~100+ to ~30–40 for a typical response, keeping the UI smooth.

### 8.4 SQLite Concurrency

SQLite with `check_same_thread=False` allows the database to be used across FastAPI's thread pool. SQLite's write locking means only one write can occur at a time — not an issue for a single-user application. The `echo=True` flag logs every SQL statement; disabling it removes a small I/O cost per query.

### 8.5 Embedding Consistency

When an item is updated and re-embedded, there is a brief window where the SQLite record reflects the new data but Pinecone still holds the old embedding. This window closes when the background task completes (~300ms). For a single-user personal archive, this eventual consistency is acceptable.

If `image_url` is the only field changed, re-embedding is intentionally skipped (the `_EMBEDDING_FIELDS` set check) since `image_url` is not part of the embedding text.

---

## 9. Development Environment

### 9.1 Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Backend runtime |
| uv | latest | Python package management |
| Node.js | 20+ | Frontend build toolchain |
| pnpm | 9+ | Node package management |
| Pinecone account | — | Vector index (free tier) |
| OpenAI API key | — | Embeddings (`text-embedding-3-small`) |
| Anthropic API key | — | Chat generation (Claude Sonnet) |

### 9.2 Project Structure

```
wavelength-app/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── items.py       # All item endpoints
│   │   ├── core/
│   │   │   └── config.py          # Pydantic Settings (env vars)
│   │   ├── services/
│   │   │   ├── conversation.py    # In-memory chat history store
│   │   │   ├── embeddings.py      # OpenAI + Pinecone operations
│   │   │   └── rag.py             # LangChain chains, LLM calls
│   │   ├── database.py            # SQLite engine + session factory
│   │   ├── main.py                # FastAPI app + CORS
│   │   ├── models.py              # SQLModel ORM (Item, ItemType)
│   │   └── schemas.py             # Pydantic request/response schemas
│   ├── pyproject.toml
│   └── .env                       # Not committed — see .env.example
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── items.ts           # Axios API layer
│   │   ├── components/            # React UI components
│   │   ├── hooks/                 # TanStack Query + streaming hooks
│   │   ├── lib/
│   │   │   └── api.ts             # Axios instance (reads VITE_API_URL)
│   │   ├── stores/
│   │   │   └── uiStore.ts         # Zustand (activeTab, modal, selections)
│   │   └── types/
│   │       └── item.ts            # TypeScript interfaces
│   ├── .env                       # Not committed — see .env.example
│   └── .env.example
└── DESIGN.md
```

### 9.3 Local Setup

**Backend:**
```bash
cd backend
uv sync                          # Install Python dependencies
cp .env.example .env             # Then fill in API keys
uv run uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
pnpm install
cp .env.example .env             # Set VITE_API_URL=http://localhost:8000
pnpm dev                         # Starts Vite dev server on :5173
```

### 9.4 Environment Variables

**Backend (`.env`):**
```
DATABASE_URL=sqlite:///./wavelength.db
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=pcsk_...
ANTHROPIC_API_KEY=sk-ant-...
LANGCHAIN_API_KEY=ls__...          # Optional — enables LangSmith tracing
LANGCHAIN_TRACING_V2=true          # Optional — enables LangSmith tracing
LANGCHAIN_PROJECT=wavelength       # Optional — LangSmith project name
SECRET_KEY=dev-secret-key-replace-in-production
```

**Frontend (`.env`):**
```
VITE_API_URL=http://localhost:8000
```

The `VITE_` prefix is required for Vite to expose variables to client-side code via `import.meta.env`. Variables without this prefix remain server-side only. Backend variables are loaded by Pydantic Settings (`BaseSettings` with `env_file=".env"`) and are **not** written to `os.environ` — external SDK clients receive keys explicitly (e.g., `ChatAnthropic(api_key=settings.ANTHROPIC_API_KEY)`).

### 9.5 Pinecone Index Setup

The index must exist before the backend starts. The index is named `wavelength-dev` and is hard-coded in `embeddings.py`:

```python
index = pinecone_client.Index("wavelength-dev")
```

Create the index in the Pinecone console with:
- **Dimensions:** 1536 (matches `text-embedding-3-small`)
- **Metric:** cosine
- **Pod type:** starter (free tier)

---

## 10. Deployment Architecture

### 10.1 Current State (Local Development Only)

The application currently runs as two local processes communicating over localhost:

```
Browser (localhost:5173)
        │
        │  HTTP / SSE
        ▼
FastAPI (localhost:8000)
   ├── SQLite file (./wavelength.db)
   ├── Pinecone (cloud, us-east-1)
   ├── OpenAI API (cloud)
   └── Anthropic API (cloud)
```

There is no containerization, reverse proxy, or production deployment. Both services are started manually in separate terminals.

### 10.2 CORS Configuration

The FastAPI app allows requests from the Vite dev server origin:

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 10.3 Path to Production (Not Yet Implemented)

A production deployment would require:

1. **Containerization** — Dockerfiles for backend and frontend
2. **Reverse proxy** — nginx or Caddy in front of FastAPI; serve built frontend static files
3. **Database** — Migrate from SQLite to PostgreSQL for concurrent access and durability
4. **Authentication** — JWT-based auth (scaffolded in `config.py` with `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` — not yet wired up)
5. **Environment** — Secrets management via cloud provider (AWS Secrets Manager, etc.)
6. **Persistent conversation memory** — Replace in-memory dict with Redis or database-backed storage

---

## 11. Security Considerations

### 11.1 Current Posture

| Concern | Status | Notes |
|---|---|---|
| API key exposure | Mitigated | Keys in `.env`, not committed; `.gitignore` covers both `backend/.env` and `frontend/.env` |
| Authentication | Not implemented | Single-user app; no auth layer exists |
| SQL injection | Not applicable | SQLModel/SQLAlchemy uses parameterized queries exclusively |
| XSS | Low risk | React escapes content by default; no `dangerouslySetInnerHTML` usage |
| CORS | Restricted | Only `localhost:5173` allowed; would need updating for production |
| Input validation | Partial | Pydantic validates request bodies; `year` field has range constraint (`ge=1700, le=2100`) |

### 11.2 Key Security Decisions

**Environment Variables Over Hardcoded Secrets:**
All API keys are loaded from `.env` via Pydantic Settings. The `.env` files are `.gitignore`d in both `backend/` and `frontend/`. `.env.example` files with placeholder values are committed instead.

**Explicit API Key Passing:**
`ChatAnthropic` and OpenAI clients receive keys explicitly as constructor arguments rather than relying on environment variable fallback:

```python
llm = ChatAnthropic(
    model_name="claude-sonnet-4-20250514",
    max_tokens_to_sample=1024,
    api_key=settings.ANTHROPIC_API_KEY,
)
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
```

This makes the key provenance explicit and avoids surprises if `os.environ` is not populated.

**Parameterized Queries:**
All database access goes through SQLModel (which wraps SQLAlchemy). Query parameters are always passed as bound parameters, never string-interpolated.

### 11.3 Auth Scaffold (Not Yet Wired)

`config.py` declares three auth-related settings that are not currently used:

```python
SECRET_KEY: str = "dev-secret-key-replace-in-production"
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
```

These are placeholders for a future JWT implementation. The default `SECRET_KEY` must be replaced with a cryptographically random value before any multi-user deployment.

---

## 12. Implementation Checklist

### Backend

- [x] SQLite database with SQLModel ORM
- [x] Full CRUD endpoints for items (`POST`, `GET`, `PUT`, `DELETE`)
- [x] Item type enum (`album`, `film`, `book`, `person`, `place`)
- [x] Pydantic Settings for centralized configuration (`app/core/config.py`)
- [x] OpenAI embeddings (`text-embedding-3-small`, 1536 dims)
- [x] Pinecone vector storage with cosine similarity search
- [x] Background task embedding on create and update
- [x] `_EMBEDDING_FIELDS` guard to skip unnecessary re-embedding
- [x] `model_copy()` snapshot pattern for safe background task passing
- [x] Semantic search endpoint (`GET /items/search`)
- [x] LangChain LCEL chain for connection finding
- [x] LangChain LCEL chain with `RunnableWithMessageHistory` for taste chat
- [x] In-memory conversation store keyed by `session_id`
- [x] SSE streaming endpoint (`POST /items/ask/stream`)
- [x] Correct async/sync route disposition (sync for blocking I/O, async only for BackgroundTasks/generators)
- [x] Error surfacing in streaming generator (`try/except` → SSE error event)
- [x] Directory structure: `app/api/routes/items.py`

### Frontend

- [x] Vite + React 19 + TypeScript
- [x] Axios instance with `VITE_API_URL` env var
- [x] TanStack Query v5 for server state (`useQuery`, `useMutation`, `invalidateQueries`)
- [x] Zustand store for shared UI state (`activeTab`, `isModalOpen`, `selectedItemIds`)
- [x] Tab navigation (`Collection`, `Chat`, `Insights`)
- [x] Add item form with modal
- [x] Edit item form (pre-filled, per-card modal)
- [x] Item list with type filter tabs
- [x] Semantic search with `use-debounce` (300ms)
- [x] SSE streaming chat hook (`useStreamingChat`)
- [x] Chunked render optimization (update UI every 3 chunks)
- [x] Find Connections feature with multi-select and Zustand state
- [x] `VITE_API_URL` environment variable (no hardcoded URLs)

### Not Yet Implemented

- [ ] User authentication (JWT scaffolded in config but not wired)
- [ ] Persistent conversation history (currently in-memory, lost on restart)
- [ ] API retry logic for transient failures (e.g., Anthropic 529 overload)
- [ ] Production deployment (Docker, reverse proxy, PostgreSQL)
- [ ] Image upload / cover art fetching
- [ ] Rate limiting

---

## 13. Known Limitations & Future Work

### 13.1 In-Memory Conversation History

**Current behavior:** Conversation histories are stored in a module-level dict in `conversation.py`:

```python
conversations: dict[str, InMemoryChatMessageHistory] = {}
```

**Limitation:** All chat history is lost when the backend process restarts. Each browser session uses a UUID-based `session_id` generated at component mount; if the user refreshes the page, a new session starts even before any restart.

**Future:** Replace with a persistent store — Redis with LangChain's `RedisChatMessageHistory`, or a `ConversationHistory` table in the database.

### 13.2 No Authentication

The API has no authentication layer. Any process that can reach `localhost:8000` can read and modify the collection. This is acceptable for a single-user local application but must be addressed before any network-accessible deployment.

**Future:** Implement JWT-based auth with `python-jose` and `passlib`. The `SECRET_KEY`, `ALGORITHM`, and `ACCESS_TOKEN_EXPIRE_MINUTES` settings are already declared in `config.py`.

### 13.3 No Retry Logic for External APIs

API calls to OpenAI, Pinecone, and Anthropic can fail transiently (rate limits, temporary overload). Currently, failures propagate as exceptions. In the streaming endpoint, the `try/except` in the async generator converts exceptions into SSE error events readable by the client, but no retry is attempted.

**Future:** Add retry logic with exponential backoff using `tenacity` for embedding generation and LLM calls.

### 13.4 SQLite Scalability

SQLite is appropriate for a single-user local application. It does not support concurrent writes, and the database file is a single point of failure with no built-in backup.

**Future:** Migrate to PostgreSQL with Alembic migrations for multi-user or network-accessible deployments.

### 13.5 Pinecone Index Name is Hardcoded

The index name `"wavelength-dev"` is hardcoded in `embeddings.py`. This means the production and development environments share the same index unless the code is manually changed.

**Future:** Move the index name to `config.py` as an environment variable (e.g., `PINECONE_INDEX_NAME`).

### 13.6 LangChain Model Name is Hardcoded

The model string `"claude-sonnet-4-20250514"` is repeated in all three `ChatAnthropic` instantiations in `rag.py`. Any model upgrade requires changing three lines.

**Future:** Extract to `config.py` as `LLM_MODEL: str = "claude-sonnet-4-20250514"`.

### 13.7 Missing Features

- **Image support:** The `image_url` field exists in the data model and schema but no UI for uploading or fetching cover art is implemented.
- **Bulk import:** No way to import a collection from CSV, Letterboxd export, or similar.
- **Export:** No way to export the collection.
- **Recommendations:** No "you might like" inference based on the collection.

---

## 14. API Reference

Base URL (local dev): `http://localhost:8000`

### 14.1 Item Endpoints

#### `POST /items/`
Create a new item. Triggers embedding generation as a background task.

**Request body:**
```json
{
  "title": "Blood on the Tracks",
  "type": "album",
  "creator": "Bob Dylan",
  "year": 1975,
  "notes": "Raw heartbreak",
  "image_url": null
}
```

**Response:** `ItemResponse` (201)
```json
{
  "id": 1,
  "title": "Blood on the Tracks",
  "type": "album",
  "creator": "Bob Dylan",
  "year": 1975,
  "notes": "Raw heartbreak",
  "image_url": null,
  "created_at": "2026-02-20T12:00:00",
  "updated_at": "2026-02-20T12:00:00"
}
```

---

#### `GET /items/`
List all items, with optional type filter.

**Query params:**
- `type` (optional): `album` | `film` | `book` | `person` | `place`
- `limit` (optional, default 100): max items to return

**Response:** `list[ItemResponse]`

---

#### `GET /items/{item_id}`
Get a single item by ID.

**Response:** `ItemResponse` (200) or 404

---

#### `PUT /items/{item_id}`
Update an item. Only provided fields are updated. Re-embedding is triggered as a background task only if semantic fields (`title`, `creator`, `year`, `notes`, `type`) changed.

**Request body:** any subset of `ItemCreate` fields (all optional)
```json
{ "notes": "Updated notes" }
```

**Response:** `ItemResponse` (200) or 404

---

#### `DELETE /items/{item_id}`
Delete an item. Does **not** delete the corresponding Pinecone vector.

**Response:** `{ "message": "Item deleted" }` (200) or 404

---

#### `GET /items/search`
Semantic search using vector similarity.

**Query params:**
- `query` (required): natural language search string
- `limit` (optional, default 10): max results

**Response:**
```json
[
  {
    "id": 1,
    "title": "Blood on the Tracks",
    "type": "album",
    "creator": "Bob Dylan",
    "year": 1975,
    "notes": "Raw heartbreak",
    "image_url": null,
    "created_at": "...",
    "updated_at": "...",
    "score": 0.923
  }
]
```

---

#### `POST /items/connections`
Find AI-generated connections between a set of items.

**Request body:**
```json
{ "item_ids": [1, 3, 7] }
```

**Response:**
```json
{ "explanation": "These three works share a preoccupation with..." }
```

---

#### `POST /items/ask`
Ask a question about your collection (non-streaming, with conversation memory).

**Request body:**
```json
{
  "question": "What does my taste say about me?",
  "session_id": "abc-123"
}
```

**Response:**
```json
{
  "answer": "Your collection reveals a recurring theme of...",
  "sources": [{ "id": 1, "title": "Blood on the Tracks", ... }]
}
```

---

#### `POST /items/ask/stream`
Same as `/ask` but streams the answer as Server-Sent Events.

**Request body:** same as `/ask`

**Response:** `text/event-stream`
```
data: Your

data:  collection

data:  reveals

data:  a recurring theme...
```

Each `data:` line contains one token. The client strips the `data: ` prefix and concatenates tokens.

---

## 15. Error Handling

### 15.1 HTTP Errors

FastAPI returns standard HTTP error responses for predictable failure cases:

| Scenario | Status | Body |
|---|---|---|
| Item not found | 404 | `{ "detail": "Item not found" }` |
| Invalid request body | 422 | Pydantic validation error detail |
| Internal error | 500 | FastAPI default |

### 15.2 Streaming Error Propagation

For the `POST /items/ask/stream` endpoint, errors that occur inside the async generator cannot be communicated via HTTP status codes (the 200 response has already been sent when streaming begins). Instead, errors are caught and sent as SSE error events:

```python
# backend/app/api/routes/items.py
async def generate():
    try:
        for chunk in ask_about_taste_stream(
            request.question,
            session,
            request.session_id,
        ):
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0)
    except Exception as e:
        yield f"data: [Error: {type(e).__name__} — {e}]\n\n"
```

The client receives a final SSE message that starts with `[Error:` instead of content, making the failure visible in the chat UI rather than causing a silent hang.

**Motivation:** LangChain has a known issue where exceptions during streaming are re-raised as `httpx.ResponseNotRead`, masking the original error. This try/except surfaces the real exception type and message (e.g., `OverloadedError: 529 — {"type":"error","error":{"type":"overloaded_error",...}}`).

### 15.3 Background Task Errors

Errors in background tasks (embedding generation) are not propagated to the HTTP response — the item creation/update response has already been sent. Failures are logged to stderr but not surfaced to the user.

**Implication:** An item can exist in SQLite without a corresponding Pinecone vector if embedding generation fails. It will not appear in semantic search results but will appear in `GET /items/` list views.

### 15.4 Frontend Error Handling

The `useStreamingChat` hook wraps the fetch and reader loop in a `try/catch`:

```typescript
try {
  // fetch + SSE read loop
} catch (error) {
  console.error('Streaming error:', error)
} finally {
  setIsStreaming(false)
}
```

Network-level errors are caught and logged; `isStreaming` is always reset to `false` in `finally`. Application-level errors surfaced via SSE (the `[Error:` prefix pattern) are currently appended to the chat as assistant messages, making them visible without a separate error state.

---

## 16. Monitoring & Observability

### 16.1 LangSmith Tracing (Optional)

LangChain integrates with LangSmith for tracing chain execution. When the following environment variables are set in `.env`, every chain invocation is traced automatically:

```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=wavelength
```

Traces capture: prompt inputs, LLM outputs, token counts, latency per step, and retrieval results. No code changes are required — LangChain picks up these variables at import time.

**Note:** These variables are not declared as fields in `Settings` because they are read directly from `os.environ` by LangChain. Pydantic Settings is configured with `extra="ignore"` so they do not cause a startup validation error.

### 16.2 SQL Logging

The SQLite engine is configured with `echo=True` in `database.py`:

```python
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)
```

This logs every SQL statement to stdout, which is useful during development but adds I/O overhead. Set `echo=False` for any production deployment.

### 16.3 Debug Logging in Frontend

`useStreamingChat.ts` logs raw SSE chunk sizes to the browser console:

```typescript
console.log('Raw chunk size:', value?.length)
```

This is development instrumentation left in for visibility into streaming behavior.

### 16.4 Observability Gaps

The following are not currently instrumented:

| Gap | Impact |
|---|---|
| No structured application logging | Errors in background tasks only appear on stderr; no log aggregation |
| No request tracing | Cannot correlate frontend requests to backend processing time |
| No embedding failure alerting | Items can be created without vectors; this is silent |
| No latency metrics | No p50/p95/p99 data for AI endpoint response times |
| No Pinecone vector count monitoring | Cannot detect drift between SQLite item count and Pinecone vector count |
