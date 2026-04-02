import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models import (
    QuizGenerateRequest,
    QuizGenerateResponse,
    Question,
    AnswerRequest,
    AnswerResponse,
    QuizResultsResponse,
)
from app.config import settings
from app.services.quiz_service import quiz_service
from app.services.document_service import document_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post("/generate", response_model=QuizGenerateResponse)
async def generate_quiz(request: QuizGenerateRequest):
    if request.source_type == "topic":
        if not request.topic:
            raise HTTPException(400, "Topic is required for topic-based quizzes")
        content = request.topic
    else:
        if not request.document_id:
            raise HTTPException(400, "Document ID is required for document-based quizzes")
        doc = document_service.get_document(request.document_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        content = "\n\n".join(doc["chunks"])

    try:
        questions = await quiz_service.generate_questions(
            content=content,
            source_type=request.source_type,
            num_questions=request.num_questions,
            question_types=request.question_types,
        )
    except Exception as e:
        logger.exception("Quiz generation failed")
        raise HTTPException(502, f"LLM generation failed: {e}")

    quiz_id = quiz_service.create_quiz(questions)

    return QuizGenerateResponse(
        quiz_id=quiz_id,
        questions=[Question(**q) for q in questions],
    )


@router.get("/generate/stream")
async def generate_quiz_stream(
    source_type: str,
    topic: str | None = None,
    document_id: str | None = None,
    num_questions: int = 10,
    question_types: str = "mcq,true_false,short_answer",
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

    # Resolve content
    if source_type == "topic":
        content = topic  # type: ignore[assignment]
    else:
        doc = document_service.get_document(document_id)  # type: ignore[arg-type]
        if not doc:
            raise HTTPException(404, "Document not found")
        content = "\n\n".join(doc["chunks"])

    # Build batch plan (same logic as generate_questions)
    batch_size = settings.quiz_batch_size
    batches: list[int] = []
    remaining = num_questions
    while remaining > 0:
        size = min(batch_size, remaining)
        batches.append(size)
        remaining -= size

    async def event_generator():
        yield f"data: {json.dumps({'type': 'start', 'total': num_questions, 'batches': len(batches)})}\n\n"

        all_questions: list[dict] = []
        seen_questions: set[str] = set()

        for i, size in enumerate(batches):
            batch = await quiz_service._generate_batch(content, source_type, size, types_list, i)

            if not batch:
                yield f"data: {json.dumps({'type': 'error', 'message': f'Batch {i} returned no questions', 'batch': i})}\n\n"
                continue

            for q in batch:
                key = q["question"].strip().lower()
                if key and key not in seen_questions:
                    seen_questions.add(key)
                    all_questions.append(q)
                    yield f"data: {json.dumps({'type': 'question', 'question': q, 'index': len(all_questions) - 1})}\n\n"

        if not all_questions:
            yield f"data: {json.dumps({'type': 'error', 'message': 'All batches failed. Check Ollama connectivity.', 'fatal': True})}\n\n"
            return

        quiz_id = quiz_service.create_quiz(all_questions)
        yield f"data: {json.dumps({'type': 'complete', 'quiz_id': quiz_id, 'total': len(all_questions)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/{quiz_id}/answer", response_model=AnswerResponse)
async def submit_answer(quiz_id: str, request: AnswerRequest):
    quiz = quiz_service.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    question = quiz["questions"].get(request.question_id)
    if not question:
        raise HTTPException(404, "Question not found")

    result = await quiz_service.grade_answer(question, request.answer)

    # Store the answer
    quiz["answers"][request.question_id] = {
        "user_answer": request.answer,
        **result,
    }

    return AnswerResponse(**result)


@router.get("/{quiz_id}/results", response_model=QuizResultsResponse)
async def get_results(quiz_id: str):
    quiz = quiz_service.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    questions_list = list(quiz["questions"].values())
    answers_list = [
        quiz["answers"].get(q["id"], {"user_answer": "", "is_correct": False, "score": 0, "feedback": ""})
        for q in questions_list
    ]

    summary = await quiz_service.generate_quiz_summary(questions_list, answers_list)
    return QuizResultsResponse(**summary)
