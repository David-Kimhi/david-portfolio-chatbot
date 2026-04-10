# Portfolio Chatbot

A **Retrieval-Augmented Generation (RAG)** portfolio assistant: a **FastAPI** backend with NDJSON streaming and a **React + TypeScript** web UI (Vite), bilingual (English / Hebrew), with vector search over embedded documents.

## 🏗️ Architecture Overview

**Tech Stack:**
- **API:** FastAPI (async/await throughout)
- **Web UI:** React 19, TypeScript, Vite ([`web/`](web/)); static assets served by nginx in Docker ([`web/Dockerfile`](web/Dockerfile))
- **Vector Database:** ChromaDB with persistent storage
- **Embeddings:** SentenceTransformers (`all-MiniLM-L6-v2`)
- **LLM:** OpenAI (streaming NDJSON responses)
- **Authentication:** JWT-based with python-jose (admin ingest)
- **Containerization:** Docker Compose ([`docker-compose.yml`](docker-compose.yml), [`backend/Dockerfile`](backend/Dockerfile))

**Architecture Pattern:** Microservices-ready API with clear separation of concerns (routes, services, utilities), designed for horizontal scaling.

## 🚀 Key Features

### 1. **RAG (Retrieval-Augmented Generation)**
- Semantic search using cosine similarity over embedded documents
- Configurable top-k retrieval with similarity threshold filtering
- Context-aware prompt engineering with source attribution (see [`backend/utils/constants.py`](backend/utils/constants.py))
- Fallback handling when no relevant sources are found

### 2. **Async-First Design**
- Full async/await implementation for non-blocking I/O
- CPU-bound operations (model loading, embeddings) offloaded to thread pool via `asyncio.to_thread()`
- Streaming responses using Server-Sent Events (SSE) with NDJSON format (see [`backend/utils/responses.py`](backend/utils/responses.py))
- Efficient event loop management to prevent blocking

### 3. **Bilingual Document Processing**
- Automatic language detection (Hebrew/English)
- Hebrew documents translated to English for embedding (better semantic search)
- Original + translated text stored in vector DB for context preservation
- Language metadata tracking for source attribution

### 4. **Streaming API Endpoints**
- Real-time token streaming for LLM responses
- Graceful error handling with timeout management
- Throttling support for rate-controlled streaming

### 5. **Security & Authentication**
- JWT-based authentication with configurable expiration
- Protected ingestion endpoints (admin-only)
- Secure system prompts to prevent prompt injection
- Environment-based secret management (see [`backend/utils/settings.py`](backend/utils/settings.py))

## 📁 Project Structure

```
backend/
├── api/
│   └── [main.py](backend/api/main.py)              # FastAPI app, CORS, routes, startup
├── routes/
│   ├── [auth.py](backend/routes/auth.py)
│   └── [translate.py](backend/routes/translate.py)
├── services/
│   └── [llm.py](backend/services/llm.py)
└── utils/
    ├── [constants.py](backend/utils/constants.py)
    ├── [responses.py](backend/utils/responses.py)
    └── [settings.py](backend/utils/settings.py)

web/
├── src/                    # React app (chat UI, admin drawer, i18n, NDJSON streaming client)
├── [Dockerfile](web/Dockerfile)   # build → nginx static
└── [vite.config.ts](web/vite.config.ts)  # dev proxy: /api → http://127.0.0.1:8000
```

Python dependencies for the API are listed in [`requirements-backend.txt`](requirements-backend.txt). Root [`requirements.txt`](requirements.txt) includes that file for local `pip install -r requirements.txt`.


### Code Quality
- Type hints throughout (Python 3.10+)
- Separation of concerns (routes, business logic, utilities)
- Reusable streaming utilities
- Environment-based configuration

## 🔌 API Endpoints

### `POST /api/ask/stream`
Streaming RAG query endpoint. Embeds user question, retrieves top-k similar documents, and streams LLM response with source citations.

Implemented in [`backend/api/main.py`](backend/api/main.py).

**Request:**
```json
{
  "question": "What technologies did David use in his projects?",
  "top_k": 4
}
```

**Response:** NDJSON stream
```json
{"type":"chunk","data":"David used..."}
{"type":"chunk","data":" technologies..."}
{"type":"sources","data":[{"title":"Project X","url":"..."}]}
```

### `POST /api/ingest`
Protected endpoint for ingesting documents into the vector store. Handles bilingual text processing, translation, and embedding.

Implemented in [`backend/api/main.py`](backend/api/main.py).

**Headers:** `Authorization: Bearer <JWT>`

**Request:**
```json
[
  {
    "id": "project-1",
    "text": "Project description...",
    "meta": {"title": "Project Name", "url": "https://..."}
  }
]
```

### `POST /api/translate/stream`
Streaming translation endpoint (Hebrew ↔ English) using LLM.

Implemented in [`backend/routes/translate.py`](backend/routes/translate.py).

### `POST /api/auth/login`
JWT token generation for authenticated endpoints.

Implemented in [`backend/routes/auth.py`](backend/routes/auth.py).

## 🐳 Deployment

**Docker Compose:**
```bash
docker-compose up -d
```

See [`docker-compose.yml`](docker-compose.yml) for configuration.

The API runs on port 8000 (internal), designed to be reverse-proxied (e.g., Caddy, Nginx).

**Environment Variables (API):**
- `OPENAI_API_KEY` - OpenAI API key
- `JWT_SECRET` - Secret for JWT signing (and session middleware)
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` - Admin credentials
- `CHROMA_DIR` - Vector DB persistence path (optional: `CHROMA_DIR_FALLBACK` if the default path is not writable)
- `CORS_ORIGINS` - Comma-separated allowed browser origins (defaults include `http://localhost:5173` for Vite)

**Compose (web image build):**
- `PUBLIC_API_URL` - Passed as `VITE_API_URL` at build time. Use the **browser-reachable** API origin (e.g. `https://api.example.com`). If empty, the SPA calls **relative** `/api/...` (your reverse proxy must forward `/api` to the API service).

For production, set **`CORS_ORIGINS`** on the API to the exact origin of the static site (comma-separated).

See [`requirements-backend.txt`](requirements-backend.txt) for API dependencies.

## 💻 Local development (API + web)

1. **API** (from repo root, with `.env` for `OPENAI_API_KEY`, `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`):

   ```bash
   pip install -r requirements.txt
   uvicorn backend.api.main:app --reload --port 8000
   ```

2. **Web** — leave `VITE_API_URL` unset so the Vite dev server proxies `/api` to `http://127.0.0.1:8000` (see [`web/vite.config.ts`](web/vite.config.ts)). CORS defaults allow `http://localhost:5173`.

   ```bash
   cd web && npm install && npm run dev
   ```

   Open the URL Vite prints (usually `http://localhost:5173`). JWT for admin ingest is stored in **sessionStorage** under `portfolio_chat_jwt`.

## 🎯 Design Decisions

1. **Why FastAPI?** Async support, automatic OpenAPI docs, type validation, high performance
2. **Why ChromaDB?** Lightweight, embedded, persistent, Python-native, no external dependencies
3. **Why SentenceTransformers?** Fast, local embeddings, no API costs
4. **Why Streaming?** Better UX, lower perceived latency, memory-efficient for long responses
5. **Why Thread Pool for Embeddings?** Prevents blocking event loop while maintaining async API surface


## 🔒 Security Features

- JWT token expiration (30 minutes)
- System prompt hardening against injection attacks
- Environment variable secrets (no hardcoded credentials)

## 🧪 Testing & Monitoring

- Health check endpoint
- Structured error responses
- Timeout handling for external API calls

---

**Built with:** Python 3.11+, FastAPI, ChromaDB, SentenceTransformers, OpenAI API, React, TypeScript, Vite
