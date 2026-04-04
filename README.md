<img width="956" height="866" alt="loading" src="https://github.com/user-attachments/assets/a719a2f2-904d-41d0-b330-dcac6fef6729" /><p align="center">
  <img src="figures/learnloop-logo-stacked.svg" alt="LearnLoop Logo" width="200">
</p>

<h1 align="center">LearnLoop</h1>

<p align="center">
  <strong>AI-Powered Adaptive Study Platform</strong><br>
  Generate quizzes from any document or topic using a local LLM. Get instant feedback, score breakdowns, and Socratic coaching.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Next.js_14-000000?style=flat&logo=nextdotjs&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/Ollama-000000?style=flat&logo=ollama&logoColor=white" alt="Ollama">
  <img src="https://img.shields.io/badge/Qwen_3.5-blueviolet?style=flat" alt="Qwen 3.5">
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat&logo=tailwindcss&logoColor=white" alt="Tailwind">
</p>

---

## Screenshots

| Home & Generation | Quiz Taking | Feedback & Grading |
|:-:|:-:|:-:|
| ![Generating quiz](figures/loading.png) | ![Quiz question](figures/quiz_question.png) | ![Correct answer](figures/correct_answer.png) |

---

## What's Working Today

- **Document upload** (PDF, TXT) with text extraction and chunking
- **Progressive quiz generation via SSE** — questions stream to the browser as they're generated (no more blank loading screen)
- **Quiz generation** from uploaded documents or free-text topics (2-50 questions, MCQ + short answer + true/false mix)
- **Parallel batch generation** — up to 2-3x speedup with `OLLAMA_NUM_PARALLEL=2/3`
- **Answer submission** with instant LLM-graded feedback and explanations
- **Results page** with score breakdown, per-question review, and AI coaching summary
- **Socratic coaching chat** for post-quiz follow-up
- **Health check** endpoint with LLM connectivity status
- **In-memory caching** with TTL (configurable, designed for Redis swap later)
- **Full test suite** (unit tests for LLM, documents, quiz, and grading services)
- **Robust error handling** — partial batch failures don't crash the quiz, connection drops are gracefully recovered

**Current LLM:** Ollama + Qwen 3 1.7B (Q4_K_M quantization), running locally on CPU via WSL2. ~1.1GB VRAM, supports 2-3x parallel inference pipelines with `OLLAMA_NUM_PARALLEL=2`.

---

## Performance Benchmarks

### With Qwen 3 1.7B (Current — Fast, Trade-off: Quality)
Measured on CPU (WSL2, no GPU). Uses 1.1GB VRAM; supports 2x parallelization (3 with 4GB+ VRAM).

| Operation | Single | Dual-Parallel |
|-----------|--------|---------------|
| Health check | <1s | <1s |
| Topic quiz (3 MCQ) | ~8-12s | ~5-7s |
| Topic quiz (10 mixed) | ~25-35s | ~15-20s |
| Document upload + parse | <2s | <2s |
| Document quiz (5 questions) | ~15-25s | ~10-15s |
| Document quiz (10 questions) | ~30-45s | ~20-30s |
| Answer grading (MCQ/TF) | instant | instant |
| Answer grading (short answer) | ~3-5s | ~3-5s |
| Coaching chat response | ~5-8s | ~5-8s |
| Quiz results + AI summary | ~5-8s | ~5-8s |

**To enable 2x parallelization**, set before starting Ollama:
```bash
OLLAMA_NUM_PARALLEL=2 ollama serve
```

### Alternative: Qwen 3.5 4B (Balanced)
3.4GB model, ~3-4x faster than 9B, higher quality than 1.7B.

| Operation | Time |
|-----------|------|
| Topic quiz (10 mixed) | ~15-25s |
| Document quiz (10 questions) | ~20-35s |

### Qwen 3.5 9B (High Quality, Slower)
6.6GB model. Previous default. Best quality, slowest (~3-5min for 10 questions).

> **Recommendation**: Qwen 3 1.7B with `OLLAMA_NUM_PARALLEL=2` offers best latency (~20-30s for 10 questions). For higher quality, switch to Qwen 3.5 4B.

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- [Ollama](https://ollama.ai/) running locally with a model pulled:
  ```bash
  ollama pull qwen3:1.7b      # Current default: fastest (1.1GB VRAM), good for quick testing
  # or
  ollama pull qwen3.5:4b      # Balanced: faster than 9B, better quality than 1.7B (3.4GB VRAM)
  # or
  ollama pull qwen3.5:9b      # High quality: slower but most capable (6.6GB VRAM)
  ```

## Quick Start

```bash
# 1. Install dependencies
make setup-backend
make setup-frontend

# 2. Start Ollama with parallelization enabled (2x speedup)
OLLAMA_NUM_PARALLEL=2 ollama serve

# 3. Start both servers (new terminals)
make run-backend   # Terminal 2 — http://localhost:8000
make run-frontend  # Terminal 3 — http://localhost:3000
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Architecture

```
LearnLoop/
├── backend/              # FastAPI (Python)
│   ├── app/
│   │   ├── main.py               # App entry, CORS, routes
│   │   ├── config.py             # Settings via pydantic-settings
│   │   ├── models.py             # Request/response schemas
│   │   ├── routers/              # API endpoints (quiz, documents, chat)
│   │   ├── services/             # Business logic (LLM, quiz, documents, chat)
│   │   └── prompts/              # Prompt templates
│   └── tests/
├── frontend/             # Next.js 14 + TypeScript + Tailwind
│   └── src/
│       ├── app/                  # Pages (home, quiz, results)
│       ├── components/           # UI components
│       ├── hooks/                # useQuiz state management
│       └── lib/                  # API client, types
├── figures/              # Logos, screenshots, design assets
├── docs/                 # Implementation plan, notes
├── docker-compose.yml    # Container orchestration (WIP)
├── Makefile
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check + LLM status |
| POST | `/api/documents/upload` | Upload PDF/TXT |
| POST | `/api/quiz/generate` | Generate quiz questions (sync, returns all at once) |
| **GET** | **`/api/quiz/generate/stream`** | **Stream quiz questions progressively via SSE** ← Recommended |
| POST | `/api/quiz/{id}/answer` | Submit an answer |
| GET | `/api/quiz/{id}/results` | Get quiz results + coaching summary |
| POST | `/api/chat/coach` | Socratic coaching chat |

> **Note**: The frontend uses `/api/quiz/generate/stream` (SSE) by default for progressive rendering. The synchronous POST endpoint is still available as a fallback.

## Running Tests

```bash
make test
```

---

## Roadmap

### High Priority

These are the highest-impact items — they affect both perceived and actual performance:

- [x] **Streaming responses via SSE** — Show quiz questions to the user as they generate instead of waiting for the full batch. Eliminates the blank loading screen during long generations and gives immediate visual feedback. ✅ Implemented with keep-alive pings and error recovery.
- [x] **Parallel batch generation** — Use `OLLAMA_NUM_PARALLEL=2/3` to run multiple inference pipelines concurrently. Achieved **~2x speedup** with qwen3:1.7b using 2x parallelization. ✅ Implemented.
- [ ] **Faster LLM inference** — Current default is Qwen 3 1.7B (~25-35s/10 questions). Options to improve further:
  - Switch to `qwen3.5:4b` for better quality (~15-25s) at 3.4GB VRAM cost
  - Swap Ollama for **Groq API** (free tier, 100+ requests/day) — `llama-3.1-8b` achieves <200ms latency
  - Dedicated GPU (12GB+ VRAM) for 3-5x speedup over CPU
  - Background pre-generation queue

### Infrastructure & Persistence

- [ ] **PostgreSQL database** — Replace in-memory storage with persistent PostgreSQL. Store quiz sessions, results, documents, and user data across restarts.
- [ ] **Redis** — Add as caching layer for generated quiz sessions, LLM response caching, and (later) as Celery task queue backend.
- [ ] **Docker Compose containerization** — Fully containerize the stack (backend, frontend, PostgreSQL, Redis) with proper networking, health checks, and volume mounts for data persistence. Current `docker-compose.yml` has placeholder services only.
- [ ] **Alembic migrations** — Schema versioning and migration management for PostgreSQL.

### Reliability & Export

- [ ] **Results export as PDF** — Let users download their quiz results, score breakdowns, and coaching feedback as a formatted PDF report.
- [ ] **Error recovery** — Graceful handling of LLM timeouts, malformed JSON responses, and partial generation failures.
- [ ] **Session persistence** — Resume interrupted quiz sessions after page refresh or disconnect.

### Future

- [ ] Auth system (JWT registration/login)
- [ ] Spaced repetition scheduling (SM-2)
- [ ] Flashcard generation and review
- [ ] Analytics dashboard with mastery tracking
- [ ] Multi-format upload (DOCX, PPTX) with OCR fallback
- [ ] Embedding-based semantic search (pgvector)
- [ ] Background processing with Celery workers

---

## Switching LLM Providers

The LLM service uses an abstract base class (`BaseLLMService`). To add a new provider:
1. Create a new class extending `BaseLLMService` in `llm_service.py`
2. Implement `generate()`, `generate_json()`, and `health_check()`
3. Update the singleton instance based on a config flag

---

## License

MIT
