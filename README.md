# Portfolio Chatbot - Backend API

A production-ready **Retrieval-Augmented Generation (RAG)** chatbot API built with FastAPI, featuring bilingual support, streaming responses, and vector similarity search. This backend powers an intelligent portfolio assistant that answers questions about projects, experience, and technical skills using semantic search over embedded documents.

## 🏗️ Architecture Overview

**Tech Stack:**
- **Framework:** FastAPI (async/await throughout)
- **Vector Database:** ChromaDB with persistent storage
- **Embeddings:** SentenceTransformers (`all-MiniLM-L6-v2`)
- **LLM:** OpenAI GPT-4o-mini (streaming responses)
- **Authentication:** JWT-based with python-jose
- **Containerization:** Docker with docker-compose orchestration (see [`docker-compose.yml`](docker-compose.yml), [`backend/Dockerfile`](backend/Dockerfile))

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
│   └── [main.py](backend/api/main.py)              # FastAPI app, route registration, startup events
├── routes/
│   ├── [auth.py](backend/routes/auth.py)              # JWT authentication & authorization
│   └── [translate.py](backend/routes/translate.py)         # Bilingual translation endpoints
├── services/
│   └── [llm.py](backend/services/llm.py)               # LLM client configuration
└── utils/
    ├── [constants.py](backend/utils/constants.py)          # Configuration constants, prompts
    ├── [responses.py](backend/utils/responses.py)          # Streaming response utilities
    └── [settings.py](backend/utils/settings.py)           # ChromaDB client, OpenAI client setup
```


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

**Environment Variables:**
- `OPENAI_API_KEY` - OpenAI API key
- `JWT_SECRET` - Secret for JWT signing
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` - Admin credentials
- `CHROMA_PERSIST_DIR` - Vector DB persistence path

See [`requirements.txt`](requirements.txt) for Python dependencies.

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

**Built with:** Python 3.10+, FastAPI, ChromaDB, SentenceTransformers, OpenAI API
