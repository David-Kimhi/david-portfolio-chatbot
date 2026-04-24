# Portfolio Chatbot

A **Retrieval-Augmented Generation (RAG)** portfolio assistant: a **FastAPI** backend with NDJSON streaming and a **React + TypeScript** web UI (Vite), bilingual (English / Hebrew), with vector search over embedded documents.

## Architecture Overview

**Tech Stack:**
- **API:** FastAPI (async/await throughout)
- **Web UI:** React 19, TypeScript, Vite ([`web/`](web/)); static assets served by nginx in Docker ([`web/Dockerfile`](web/Dockerfile))
- **Vector Database:** ChromaDB with persistent storage
- **Embeddings:** SentenceTransformers (`all-MiniLM-L6-v2`)
- **LLM:** OpenAI (streaming NDJSON responses)
- **Authentication:** JWT-based with python-jose (admin endpoints)
- **Analytics:** PostgreSQL via asyncpg (event logging, usage stats)
- **Containerization:** Docker Compose ([`docker-compose.yml`](docker-compose.yml))

## Key Features

### 1. RAG with Hypothetical Question Indexing

At ingest time, each document goes through two storage passes:

1. **Document chunks** — the raw content, embedded and stored with `entry_type: "document"`. Used to build the LLM prompt.
2. **Retrieval questions** — the LLM generates 10–15 questions that the document can answer (e.g. "What is David's experience with PySpark?"). These are embedded and stored with `entry_type: "question"`.

At query time, the user's question is compared against the **generated questions** (not raw document text). This dramatically improves precision: off-topic queries like "how do I install PySpark?" score low because they don't resemble biographical questions, even if they share keywords with the document.

### 2. Conversation Context Blending

Each submitted question produces a blended embedding:

```
blended = 0.7 × current_query + 0.3 × previous_turn_embedding
```

This anchors follow-up questions ("tell me more", "what about X?") to the previous topic without sending raw chat history to the backend. The blended vector is returned to the frontend after each turn and sent back with the next request.

### 3. Real-Time Relevance Score

As the user types, a debounced call to `/api/relevance` returns a 0–1 score (compared against generated questions). The frontend shows a colored bar: green = on-topic, yellow = borderline, red = off-topic. No LLM is involved — purely local embedding math.

### 4. Bilingual Support (Hebrew / English)

- Automatic language detection per document and per user query
- Hebrew documents translated to English before embedding (better semantic search)
- Original text preserved in storage; both versions stored in the vector DB
- Frontend language switcher affects all UI strings (centralized in [`web/src/i18n/strings.ts`](web/src/i18n/strings.ts))

### 5. Streaming Responses

LLM responses stream as NDJSON over HTTP. The frontend reads chunks as they arrive and renders them in real time. The final event in each stream carries the source list and the updated context embedding for the next turn.

### 6. Admin Document Management

A slide-in drawer (gear icon) provides:
- Login with JWT (session-scoped, stored in `sessionStorage`)
- **Add document**: title, optional context header, source URL, and paste area
- **Edit document**: inline form pre-filled from existing metadata; triggers full re-embedding and question regeneration
- **Delete document**: removes all chunks and questions for that document
- **Context header**: a short descriptor prepended to the document before embedding (e.g. "Professional CV of David Kimhi"). Does not affect stored content, only the embedding.

### 7. Public Analytics

`GET /api/stats` returns aggregated usage data (total questions, language breakdown, average relevance). Logged to PostgreSQL in the background on every ask and relevance call, with IP hashing for privacy.

### 8. Security

- JWT expiration (30 min), admin-only ingestion endpoints
- System prompt hardening against prompt injection
- Rate limiting on `/api/ask/stream` (10 req/min via slowapi)
- Environment-based secret management

## Project Structure

```
backend/
├── api/
│   └── main.py              # FastAPI app, all endpoints, startup/shutdown
├── routes/
│   ├── auth.py              # JWT login endpoint
│   └── translate.py         # Hebrew ↔ English translation (streaming + util)
└── utils/
    ├── analytics.py         # PostgreSQL pool, event logging, stats query
    ├── chunking.py          # Document chunking strategy
    ├── constants.py         # Model name, thresholds, system prompts
    ├── logger.py            # Centralized logging (file + console)
    ├── responses.py         # stream_llm() and call_llm() helpers
    └── settings.py          # ChromaDB init, OpenAI client, env vars

web/src/
├── api/
│   └── client.ts            # All API calls: streaming, ingest, docs CRUD, relevance, stats
├── components/
│   ├── AdminDrawer.tsx/css  # Slide-in admin sidebar
│   ├── ChatThread.tsx/css   # Chat UI, relevance bar, input with char counter
│   └── Header.tsx/css       # Top bar with settings button
├── i18n/
│   └── strings.ts           # All UI strings (en/he) + preset questions
└── App.tsx                  # Root: state, send handler, context embedding ref
```

Logs are written to `logs/` (excluded from git, mounted outside the container).
ChromaDB data persists in `chroma_store/`.

## API Endpoints

### `POST /api/ask/stream`
Main RAG endpoint. Embeds question → retrieves matching questions → fetches parent documents → streams LLM answer.

**Request:**
```json
{
  "question": "What technologies did David use?",
  "top_k": 4,
  "context_embedding": [...]
}
```

**Response:** NDJSON stream
```
{"type":"chunk","data":"David used..."}
{"type":"sources","data":[{"title":"CV","url":"..."}],"context_embedding":[...]}
```

---

### `POST /api/relevance`
Returns a relevance score for the typed text (no LLM involved). Compares against generated question entries.

**Request:** `{ "text": "...", "context_embedding": [...] }`  
**Response:** `{ "score": 0.21, "context_embedding": [...] }`

---

### `POST /api/ingest` *(admin)*
Ingest one or more documents. For each document: stores chunks with `entry_type: "document"`, then calls the LLM to generate retrieval questions stored with `entry_type: "question"`.

**Headers:** `Authorization: Bearer <JWT>`

**Request:**
```json
[{
  "id": "cv",
  "text": "Full CV text...",
  "header": "Professional resume of David Kimhi, data engineer",
  "meta": { "title": "CV", "url": "https://..." }
}]
```

---

### `GET /api/docs` *(admin)*
Lists all documents (excludes generated question entries).

### `PUT /api/docs/{id}` *(admin)*
Re-embeds and re-generates questions for a document.

### `DELETE /api/docs/{id}` *(admin)*
Removes all chunks and question entries for a document.

### `POST /api/translate/stream`
Streaming Hebrew ↔ English translation.

### `POST /api/auth/login`
Returns a JWT for admin endpoints.

### `GET /api/stats`
Public aggregated usage analytics (total asks, language split, average relevance).

### `GET /api/health`
Returns `{"ok": true}`.

---

## Local Development

**Prerequisites:** Python 3.11+, Node 18+, an OpenAI API key.

1. **Backend** — from repo root, with a `.env` file:

   ```bash
   pip install -r requirements.txt
   uvicorn backend.api.main:app --reload --port 8000
   ```

   `.env` required keys:
   ```
   OPENAI_API_KEY=...
   JWT_SECRET=...
   ADMIN_EMAIL=...
   ADMIN_PASSWORD=...
   ```

2. **Frontend** — leave `VITE_API_URL` unset so Vite proxies `/api` to `http://127.0.0.1:8000`:

   ```bash
   cd web && npm install && npm run dev
   ```

   Open `http://localhost:5173`. The admin JWT is stored in `sessionStorage` under `portfolio_chat_jwt`.

---

## Docker Compose

```bash
docker-compose up -d
```

Services:
- `portfoliochat-api` — FastAPI backend on port 8000 (internal)
- `portfoliochat-web` — nginx static frontend on port 3000
- `portfoliochat-db` — PostgreSQL for analytics

**Environment variables (API):**

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `JWT_SECRET` | Secret for JWT signing |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Admin credentials |
| `CHROMA_DIR` | ChromaDB persistence path |
| `CORS_ORIGINS` | Comma-separated allowed origins (default: `http://localhost:5173`) |
| `DATABASE_URL` | PostgreSQL DSN (e.g. `postgresql://user:pass@db:5432/chatbot`) |

**Frontend build variable:**

| Variable | Description |
|---|---|
| `PUBLIC_API_URL` | Browser-reachable API origin, passed as `VITE_API_URL` at build time. Leave empty to use relative `/api/...` (requires reverse proxy to forward `/api` to the API service). |

---

## Design Decisions

| Decision | Rationale |
|---|---|
| Hypothetical question indexing | Separates retrieval space from document space — query-to-question matching is far more precise than query-to-document for a personal portfolio |
| Embedding blending (70/30) | Follow-up questions stay anchored to topic without sending raw chat history |
| `all-MiniLM-L6-v2` | Fast, local, no API cost — good enough for question-to-question similarity |
| ChromaDB | Lightweight, embedded, Python-native, no external service needed in dev |
| PostgreSQL for analytics | Durable event log; decoupled from ChromaDB; async via asyncpg |
| NDJSON streaming | Lower perceived latency; memory-efficient for long responses |
| `asyncio.to_thread()` for embeddings | Keeps the event loop free during CPU-bound encoding |

---

**Built with:** Python 3.11+, FastAPI, ChromaDB, SentenceTransformers, OpenAI API, PostgreSQL, asyncpg, React 19, TypeScript, Vite, nginx
