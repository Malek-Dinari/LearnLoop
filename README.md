<p align="center">
  <img src="figures/learnloop-logo-stacked.png" alt="LearnLoop Logo" width="180">
</p>

<h1 align="center">LearnLoop</h1>

<p align="center">
  <strong>AI-Powered Adaptive Study Platform</strong><br>
  Generate quizzes from any document or topic. Get instant feedback, score breakdowns, and Socratic coaching.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Next.js_14-000000?style=flat&logo=nextdotjs&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat&logo=tailwindcss&logoColor=white" alt="Tailwind">
  <img src="https://img.shields.io/badge/Ollama-000000?style=flat&logo=ollama&logoColor=white" alt="Ollama">
  <img src="https://img.shields.io/badge/Groq-F55036?style=flat&logo=groq&logoColor=white" alt="Groq">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white" alt="Docker">
</p>

---

## Screenshots

| Home & Generation | Quiz Taking | Feedback & Grading |
|:-:|:-:|:-:|
| ![Generating quiz](figures/loading.png) | ![Quiz question](figures/quiz_question.png) | ![Correct answer](figures/correct_answer.png) |

---

## What's Working

- **Document upload** — PDF and TXT with text extraction and chunking
- **Progressive quiz generation via SSE** — questions stream to the browser as they're generated, with keep-alive pings and graceful disconnect recovery
- **Topic-based quiz generation** — no document needed; ask about any subject
- **Question types** — MCQ, true/false, and short answer; configurable mix per quiz
- **Instant grading** — MCQ and true/false graded instantly; short answers scored by the LLM with per-question feedback
- **Results page** — score breakdown, per-question review, and an AI-generated coaching summary
- **Socratic coaching chat** — post-quiz follow-up for any question
- **Multi-provider LLM** — run locally with **Ollama** (any model) or switch to **Groq** cloud API with a single env var; factory pattern, zero code changes
- **Pluggable cache** — in-memory by default, drops into Redis with `CACHE_BACKEND=redis`
- **PostgreSQL persistence** — optional; set `USE_DATABASE=true` to persist quizzes, documents, and answers across restarts via SQLAlchemy + Alembic; defaults to in-memory for local dev
- **Docker Compose** — one command to start the full stack (backend, frontend, PostgreSQL, Redis) with health-check chaining and named volumes
- **Structured logging** — human-readable in dev, JSON in production; request ID on every response
- **CI** — GitHub Actions runs the full test suite on every push (no external services required)
- **51 tests** — unit and integration tests for LLM services, caching, grading, document processing, and database round-trips; DB tests run against in-memory SQLite, no PostgreSQL server needed

---

## LLM Providers

LearnLoop supports two backends, switchable via a single environment variable:

| Provider | Config | Best for |
|----------|--------|----------|
| **Ollama** (default) | `LLM_PROVIDER=ollama` | Local dev, full privacy, no API key |
| **Groq** | `LLM_PROVIDER=groq` | Fast cloud inference, free tier available |

### Recommended local models (Ollama)

```bash
ollama pull qwen3:1.7b      # Fastest — 1.1GB, good for quick testing
ollama pull qwen3.5:4b      # Balanced — 3.4GB, better quality
ollama pull qwen3.5:9b      # High quality — 6.6GB, slower
```

### Performance benchmarks

#### Groq — `llama-3.3-70b-versatile` (cloud, free tier)

| Operation | Time |
|-----------|------|
| Quiz question (1 question / call) | ~1–3s |
| 8-question quiz (sequential, 1 per call) | ~12–25s |
| Document upload + parse | <2s |
| Answer grading (MCQ/TF) | instant |
| Answer grading (short answer) | ~2–4s |

#### Ollama — Qwen 3 1.7B (local CPU, WSL2)

| Operation | Single | Dual-Parallel |
|-----------|--------|---------------|
| Topic quiz (10 mixed) | ~25–35s | ~15–20s |
| Document quiz (10 questions) | ~30–45s | ~20–30s |
| Answer grading (short answer) | ~3–5s | ~3–5s |

Enable 2x parallel inference with:
```bash
OLLAMA_NUM_PARALLEL=2 ollama serve
```

---

## Quick Start

### Local (no Docker)

```bash
# 1. Install dependencies
make setup-backend
make setup-frontend

# 2. Configure backend (copy and edit)
cp backend/.env.example backend/.env
# Set LLM_PROVIDER=ollama (default) or LLM_PROVIDER=groq + GROQ_API_KEY=...

# 3. Start backend + frontend
make run-backend   # http://localhost:8000
make run-frontend  # http://localhost:3000
```

### Docker Compose (full stack)

```bash
# Copy and edit the environment file
cp backend/.env.example backend/.env
# Set GROQ_API_KEY if using Groq, or leave LLM_PROVIDER=ollama

make docker-up     # builds images, starts all 4 services
make docker-down   # stop
make docker-reset  # stop + delete all data volumes
```

The backend auto-runs `alembic upgrade head` on startup when `USE_DATABASE=true` (set automatically in Docker Compose).

---

## Configuration

All settings are controlled via environment variables (or `backend/.env`). See [`backend/.env.example`](backend/.env.example) for the full reference.

Key options:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama` or `groq` |
| `GROQ_API_KEY` | — | Required when `LLM_PROVIDER=groq` |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Any model available on Groq |
| `OLLAMA_MODEL` | `qwen3:1.7b` | Any locally-pulled Ollama model |
| `USE_DATABASE` | `false` | `true` to enable PostgreSQL persistence |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `CACHE_BACKEND` | `memory` | `memory` or `redis` |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `QUIZ_BATCH_SIZE` | `1` | Questions per LLM call (raise to 2–4 with Ollama or paid Groq) |
| `LOG_FORMAT` | `text` | `text` (dev) or `json` (production) |

---

## Architecture

```
LearnLoop/
├── backend/                  # FastAPI (Python 3.12)
│   ├── app/
│   │   ├── main.py           # App entry, middleware, startup/shutdown hooks
│   │   ├── config.py         # Pydantic Settings — all config from env vars
│   │   ├── models.py         # Request/response Pydantic schemas
│   │   ├── database.py       # Async SQLAlchemy engine + get_db() dependency
│   │   ├── db_models.py      # ORM models: Document, Quiz, Question, Answer
│   │   ├── logging_config.py # Structured logging (text / JSON)
│   │   ├── middleware.py     # RequestID middleware (skips SSE endpoints)
│   │   ├── routers/          # API routes: quiz, documents, chat
│   │   ├── services/
│   │   │   ├── llm_service.py        # BaseLLMService ABC + Ollama impl + factory
│   │   │   ├── groq_llm_service.py   # Groq provider
│   │   │   ├── quiz_service.py       # Quiz generation, grading, dual-path persistence
│   │   │   ├── document_service.py   # Upload, chunking, dual-path persistence
│   │   │   ├── cache_service.py      # CacheBackend protocol + factory
│   │   │   └── redis_cache.py        # Redis cache backend
│   │   └── prompts/          # LLM prompt templates
│   ├── alembic/              # Database migrations
│   ├── tests/                # 51 tests (pytest + pytest-asyncio)
│   ├── Dockerfile
│   └── entrypoint.sh         # Runs migrations then starts uvicorn
├── frontend/                 # Next.js 14 + TypeScript + Tailwind
│   ├── src/
│   │   ├── app/              # Pages: home, quiz, results
│   │   ├── components/       # UI components
│   │   ├── hooks/            # useQuiz state + SSE handling
│   │   └── lib/              # API client, types
│   └── Dockerfile            # Multi-stage build with standalone output
├── .github/workflows/ci.yml  # GitHub Actions CI
├── docker-compose.yml        # postgres + redis + backend + frontend
├── Makefile
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check — LLM, DB, and cache status |
| POST | `/api/documents/upload` | Upload PDF or TXT |
| POST | `/api/quiz/generate` | Generate quiz (sync) |
| **GET** | **`/api/quiz/generate/stream`** | **Stream quiz questions via SSE** ← recommended |
| POST | `/api/quiz/{id}/answer` | Submit an answer |
| GET | `/api/quiz/{id}/results` | Results + AI coaching summary |
| POST | `/api/chat/coach` | Socratic coaching chat |

---

## Running Tests

```bash
make test
# or directly:
cd backend && python -m pytest tests/ -v
```

Tests run entirely without external services — LLM calls are mocked, the DB fixture uses SQLite in-memory, and the Redis fixture uses fakeredis.

---

## Roadmap

### Completed

- [x] SSE streaming quiz generation with keep-alive and disconnect recovery
- [x] Parallel batch generation (Ollama `OLLAMA_NUM_PARALLEL`)
- [x] Multi-provider LLM: Ollama and Groq with factory pattern
- [x] Pluggable cache: in-memory and Redis
- [x] PostgreSQL persistence with dual-path services (in-memory or DB)
- [x] Alembic migrations
- [x] Docker Compose — full stack containerization with health checks
- [x] Structured JSON logging + request ID middleware
- [x] CI pipeline (GitHub Actions)
- [x] Full test suite — unit + DB integration, no external services required

### What's Next

- [ ] **User accounts** — registration, login, and session management
- [ ] **Flashcard mode** — generate and review flashcards from documents or quiz results
- [ ] **Spaced repetition** — schedule reviews based on performance (SM-2 algorithm)
- [ ] **Progress tracking** — mastery scores and learning analytics per topic
- [ ] **Results export** — download quiz results and feedback as PDF
- [ ] **Broader document support** — DOCX, PPTX, and other formats
- [ ] **Semantic search** — find relevant content across uploaded documents

---

## License

MIT
