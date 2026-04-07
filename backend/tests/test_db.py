"""Database persistence tests using an in-memory SQLite session (no PostgreSQL needed).

These tests exercise the DB code paths in document_service and quiz_service
by passing the SQLite fixture session (conftest.py) directly to service methods.
"""

import pytest
from app.services.document_service import DocumentService
from app.services.quiz_service import QuizService


# ---------------------------------------------------------------------------
# Document DB tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_persist_and_fetch_document(db, tmp_path):
    """process_upload → _persist_document → _get_document_db round-trip."""
    svc = DocumentService()
    svc.upload_dir = str(tmp_path)

    result = await svc.process_upload("hello.txt", b"Hello world content.", db)
    assert "document_id" in result
    doc_id = result["document_id"]

    # Fetch via DB path
    doc = await svc.get_document(doc_id, db)
    assert doc is not None
    assert doc["filename"] == "hello.txt"
    assert "Hello world content" in doc["text"]
    assert isinstance(doc["chunks"], list)
    assert len(doc["chunks"]) >= 1


@pytest.mark.asyncio
async def test_get_missing_document_returns_none(db):
    """Fetching a non-existent document_id returns None (no exception)."""
    svc = DocumentService()
    result = await svc.get_document("00000000-0000-0000-0000-000000000000", db)
    assert result is None


# ---------------------------------------------------------------------------
# Quiz DB tests
# ---------------------------------------------------------------------------

SAMPLE_QUESTIONS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "type": "mcq",
        "question": "What is 2 + 2?",
        "options": ["1", "2", "3", "4"],
        "correct_answer": "4",
        "explanation": "Basic arithmetic.",
        "difficulty": "easy",
        "source_chunk": None,
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "type": "true_false",
        "question": "The sky is blue.",
        "options": ["True", "False"],
        "correct_answer": "True",
        "explanation": "It is.",
        "difficulty": "easy",
        "source_chunk": None,
    },
]


@pytest.mark.asyncio
async def test_create_and_get_quiz(db):
    """create_quiz → _create_quiz_db → get_quiz → _get_quiz_db round-trip."""
    svc = QuizService()

    quiz_id = await svc.create_quiz(
        SAMPLE_QUESTIONS, db, source_type="topic", topic="math"
    )
    assert isinstance(quiz_id, str) and len(quiz_id) > 0

    quiz = await svc.get_quiz(quiz_id, db)
    assert quiz is not None
    assert len(quiz["questions"]) == 2
    q_ids = set(quiz["questions"].keys())
    assert "11111111-1111-1111-1111-111111111111" in q_ids
    assert "22222222-2222-2222-2222-222222222222" in q_ids


@pytest.mark.asyncio
async def test_get_missing_quiz_returns_none(db):
    svc = QuizService()
    result = await svc.get_quiz("00000000-0000-0000-0000-000000000000", db)
    assert result is None


@pytest.mark.asyncio
async def test_save_and_retrieve_answer(db):
    """save_answer persists an answer row and get_quiz loads it back."""
    svc = QuizService()

    quiz_id = await svc.create_quiz(
        SAMPLE_QUESTIONS, db, source_type="topic", topic="math"
    )

    answer_data = {
        "user_answer": "4",
        "is_correct": True,
        "score": 1.0,
        "feedback": "Correct!",
        "correct_answer": "4",
    }
    await svc.save_answer(
        "11111111-1111-1111-1111-111111111111", answer_data, db
    )

    # Re-fetch quiz — answer should be loaded via selectinload
    quiz = await svc.get_quiz(quiz_id, db)
    assert quiz is not None
    ans = quiz["answers"].get("11111111-1111-1111-1111-111111111111")
    assert ans is not None
    assert ans["user_answer"] == "4"
    assert ans["is_correct"] is True
    assert ans["score"] == 1.0


@pytest.mark.asyncio
async def test_save_answer_upsert(db):
    """save_answer replaces an existing answer (upsert behaviour)."""
    svc = QuizService()

    quiz_id = await svc.create_quiz(
        SAMPLE_QUESTIONS, db, source_type="topic", topic="math"
    )

    q_id = "11111111-1111-1111-1111-111111111111"

    first = {"user_answer": "3", "is_correct": False, "score": 0.0, "feedback": "Wrong", "correct_answer": "4"}
    await svc.save_answer(q_id, first, db)

    second = {"user_answer": "4", "is_correct": True, "score": 1.0, "feedback": "Correct!", "correct_answer": "4"}
    await svc.save_answer(q_id, second, db)

    quiz = await svc.get_quiz(quiz_id, db)
    assert quiz["answers"][q_id]["user_answer"] == "4"
    assert quiz["answers"][q_id]["is_correct"] is True
