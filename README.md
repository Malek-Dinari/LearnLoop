# LearnLoop - AI-Powered Study Platform

LearnLoop is an adaptive study platform that uses a local AI (Ollama + Qwen 3.5) to generate quizzes from uploaded documents or any topic. It provides immediate feedback, score breakdowns, and Socratic coaching to help you learn effectively.

## Prerequisites

- Python 3.11+
- Node.js 20+
- [Ollama](https://ollama.ai/) running locally with the `qwen3.5:9b` model pulled:
  ```bash
  ollama pull qwen3.5:9b
  ```

## Quick Start

```bash
# 1. Install dependencies
make setup-backend
make setup-frontend

# 2. Make sure Ollama is running
ollama serve

# 3. Start both servers
make run-backend   # Terminal 1 — http://localhost:8000
make run-frontend  # Terminal 2 — http://localhost:3000
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Architecture

```
LearnLoop/
├── backend/          # FastAPI (Python)
│   ├── app/
│   │   ├── main.py           # App entry, CORS, routes
│   │   ├── config.py         # Settings via pydantic-settings
│   │   ├── models.py         # Request/response schemas
│   │   ├── routers/          # API endpoints (quiz, documents, chat)
│   │   ├── services/         # Business logic (LLM, quiz, documents, chat)
│   │   └── prompts/          # Prompt templates
│   └── tests/
├── frontend/         # Next.js 14 + TypeScript + Tailwind
│   └── src/
│       ├── app/              # Pages (home, quiz, results)
│       ├── components/       # UI components
│       ├── hooks/            # useQuiz state management
│       └── lib/              # API client, types
├── Makefile
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check + LLM status |
| POST | `/api/documents/upload` | Upload PDF/TXT |
| POST | `/api/quiz/generate` | Generate quiz questions |
| POST | `/api/quiz/{id}/answer` | Submit an answer |
| GET | `/api/quiz/{id}/results` | Get quiz results + coaching |
| POST | `/api/chat/coach` | Socratic coaching chat |

## Running Tests

```bash
make test
```

## Switching LLM Providers

The LLM service uses an abstract base class (`BaseLLMService`). To add a new provider:
1. Create a new class extending `BaseLLMService` in `llm_service.py`
2. Implement `generate()`, `generate_json()`, and `health_check()`
3. Update the singleton instance based on a config flag
