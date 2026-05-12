import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    QuizGenerateRequest,
    QuizGenerateResponse,
    Question,
    AnswerRequest,
    AnswerResponse,
    QuizResultsResponse,
)
from app.config import settings
from app.database import get_db
from app.deps import get_current_user_optional
from app.services.quiz_service import quiz_service, _is_near_duplicate, extract_topic_keywords
from app.services.document_service import document_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post("/generate", response_model=QuizGenerateResponse)
async def generate_quiz(
    request: QuizGenerateRequest,
    db: AsyncSession | None = Depends(get_db),
    user: dict | None = Depends(get_current_user_optional),
):
    if request.source_type == "topic":
        if not request.topic:
            raise HTTPException(400, "Topic is required for topic-based quizzes")
        content = request.topic
    else:
        if not request.document_id:
            raise HTTPException(400, "Document ID is required for document-based quizzes")
        doc = await document_service.get_document(request.document_id, db)
        if not doc:
            raise HTTPException(404, "Document not found")
        content = "\n\n".join(doc["chunks"])

    try:
        questions = await quiz_service.generate_questions(
            content=content,
            source_type=request.source_type,
            num_questions=request.num_questions,
            question_types=request.question_types,
            db=db,
            topic_hint=request.topic,
        )
    except Exception as e:
        logger.exception("Quiz generation failed")
        raise HTTPException(502, f"LLM generation failed: {e}")

    quiz_id = await quiz_service.create_quiz(
        questions,
        db,
        source_type=request.source_type,
        topic=request.topic,
        document_id=request.document_id,
        user_id=user["id"] if user else None,
    )

    return QuizGenerateResponse(
        quiz_id=quiz_id,
        questions=[Question(**q) for q in questions],
    )


@router.get("/generate/stream")
async def generate_quiz_stream(
    request: Request,
    source_type: str,
    topic: str | None = None,
    document_id: str | None = None,
    num_questions: int = 10,
    question_types: str = "mcq,true_false,short_answer",
    db: AsyncSession | None = Depends(get_db),
    user: dict | None = Depends(get_current_user_optional),
):
    """
    SSE endpoint for progressive quiz generation.
    Uses GET because EventSource only supports GET.

    Events emitted:
      {"type": "start",    "total": N}
      {"type": "question", "question": {...}, "index": N}
      {"type": "error",    "message": "...",  "batch": N}
      {"type": "complete", "quiz_id": "...",  "total": N}
    """
    # Validate params
    if source_type not in ("topic", "document"):
        raise HTTPException(400, "source_type must be 'topic' or 'document'")
    if source_type == "topic" and not topic:
        raise HTTPException(400, "topic is required for topic-based quizzes")
    if source_type == "document" and not document_id:
        raise HTTPException(400, "document_id is required for document-based quizzes")

    num_questions = max(1, min(num_questions, 50))
    types_list = [t.strip() for t in question_types.split(",") if t.strip()]
    if not types_list:
        types_list = ["mcq", "true_false", "short_answer"]

    # Resolve content BEFORE entering the generator so we can use the Depends session.
    # The SSE generator runs for minutes — we must not hold the session open the whole time.
    if source_type == "topic":
        content = topic  # type: ignore[assignment]
    else:
        doc = await document_service.get_document(document_id, db)  # type: ignore[arg-type]
        if not doc:
            raise HTTPException(404, "Document not found")
        content = "\n\n".join(doc["chunks"])

    # The Depends session has already committed (document fetch is read-only).
    # Close it now so we don't hold a connection during the long LLM generation.
    if db is not None:
        await db.close()

    # Build batch plan (same logic as generate_questions)
    batch_size = settings.quiz_batch_size
    batches: list[int] = []
    remaining = num_questions
    while remaining > 0:
        size = min(batch_size, remaining)
        batches.append(size)
        remaining -= size

    # Inter-batch sleep: Groq free tier has a tight tokens-per-minute limit.
    # Spacing calls out prevents bursting through the 6 000 TPM budget.
    inter_batch_sleep = (
        settings.groq_inter_batch_sleep
        if settings.llm_provider == "groq"
        else 0.0
    )

    async def event_generator():
        yield f"data: {json.dumps({'type': 'start', 'total': num_questions, 'batches': len(batches)})}\n\n"

        all_questions: list[dict] = []
        seen_questions: set[str] = set()

        for i, size in enumerate(batches):
            # Pace Groq calls to stay under the free-tier TPM rate limit.
            # Sleep BEFORE each batch (except the first) so the client
            # receives the first question as quickly as possible.
            if i > 0 and inter_batch_sleep > 0:
                logger.debug("Inter-batch sleep %.0fs (Groq rate-limit pacing)", inter_batch_sleep)
                await asyncio.sleep(inter_batch_sleep)

            # Send keep-alive ping before each LLM call so the connection
            # doesn't time out while the model generates (can take 30-60s).
            yield ": keep-alive\n\n"

            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("SSE client disconnected before batch %d", i)
                return

            # Extract seen topics from already-generated questions for diversity
            seen_topics = []
            for q in all_questions:
                keywords = extract_topic_keywords(q["question"])
                seen_topics.extend(keywords)
            # Keep only recent unique topics (limit to 12 for prompt size)
            seen_topics = list(dict.fromkeys(seen_topics))[:12]

            # Open a short-lived session per batch so EITL injection can
            # consult the DB without holding a connection across the full
            # SSE generator window.
            batch_db = None
            batch_db_cm = None
            if settings.use_database and settings.eitl_enabled:
                from app.database import async_session_factory
                batch_db_cm = async_session_factory()
                batch_db = await batch_db_cm.__aenter__()
            try:
                batch = await quiz_service._generate_batch(
                    content, source_type, size, types_list, i,
                    seen_topics=seen_topics,
                    db=batch_db,
                    topic_hint=topic if source_type == "topic" else None,
                )
            finally:
                if batch_db_cm is not None:
                    await batch_db_cm.__aexit__(None, None, None)

            if not batch:
                yield f"data: {json.dumps({'type': 'error', 'message': f'Batch {i} returned no questions', 'batch': i})}\n\n"
                continue

            for q in batch:
                key = q["question"].strip().lower()
                # Exact-match check first (fast)
                if key and key not in seen_questions:
                    # TF-IDF near-duplicate check (comprehensive but slower)
                    if not _is_near_duplicate(q, all_questions, threshold=settings.quiz_dedup_threshold):
                        seen_questions.add(key)
                        all_questions.append(q)
                        yield f"data: {json.dumps({'type': 'question', 'question': q, 'index': len(all_questions) - 1})}\n\n"

        if not all_questions:
            provider = settings.llm_provider.upper()
            yield f"data: {json.dumps({'type': 'error', 'message': f'All batches failed. Check {provider} connectivity and API key.', 'fatal': True})}\n\n"
            return

        # Persist quiz — open a short-lived session for DB mode so we don't
        # hold the request session across the entire LLM generation window.
        if settings.use_database:
            from app.database import async_session_factory
            try:
                async with async_session_factory() as session:
                    quiz_id = await quiz_service.create_quiz(
                        all_questions, session, source_type, topic, document_id,
                        user_id=user["id"] if user else None,
                    )
                    await session.commit()
            except Exception as exc:
                logger.error("Failed to persist quiz to DB, falling back to memory: %s", exc)
                quiz_id = quiz_service._create_quiz_memory(all_questions)
        else:
            quiz_id = await quiz_service.create_quiz(all_questions)

        yield f"data: {json.dumps({'type': 'complete', 'quiz_id': quiz_id, 'total': len(all_questions)})}\n\n"

    # Add CORS origin explicitly — Starlette middleware may not inject it on StreamingResponse
    origin = request.headers.get("origin", settings.cors_origins.split(",")[0])
    sse_headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
    }

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=sse_headers,
    )


@router.post("/{quiz_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    quiz_id: str,
    request: AnswerRequest,
    db: AsyncSession | None = Depends(get_db),
):
    quiz = await quiz_service.get_quiz(quiz_id, db)
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    question = quiz["questions"].get(request.question_id)
    if not question:
        raise HTTPException(404, "Question not found")

    if not request.answer.strip():
        raise HTTPException(400, "Answer cannot be empty")

    result = await quiz_service.grade_answer(question, request.answer)

    answer_data = {"user_answer": request.answer, **result}

    if db is not None and settings.use_database:
        # DB path: persist via save_answer (upserts the answer row)
        await quiz_service.save_answer(request.question_id, answer_data, db)
    else:
        # In-memory path: quiz dict is a live reference stored in quiz_service.quizzes
        quiz["answers"][request.question_id] = answer_data

    return AnswerResponse(**result)


@router.get("/{quiz_id}/results", response_model=QuizResultsResponse)
async def get_results(
    quiz_id: str,
    db: AsyncSession | None = Depends(get_db),
):
    # Check cache first to avoid LLM re-call on page refresh
    from app.services.cache_service import cache, make_cache_key

    results_cache_key = make_cache_key("results", quiz_id=quiz_id)
    cached = await cache.get(results_cache_key)
    if cached is not None:
        return QuizResultsResponse(**cached)

    quiz = await quiz_service.get_quiz(quiz_id, db)
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    questions_list = list(quiz["questions"].values())
    answers_list = [
        quiz["answers"].get(q["id"], {"user_answer": "", "is_correct": False, "score": 0, "feedback": ""})
        for q in questions_list
    ]

    summary = await quiz_service.generate_quiz_summary(questions_list, answers_list)

    # Cache results so page refresh doesn't re-call the LLM
    await cache.set(results_cache_key, summary, ttl=3600)

    return QuizResultsResponse(**summary)
