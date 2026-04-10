"""Tests for flashcard generation service and router."""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.flashcard_service import FlashcardService, _normalize_card


# ── Unit tests ─────────────────────────────────────────────────────────────

@pytest.fixture
def svc():
    return FlashcardService()


SAMPLE_QUESTIONS = [
    {
        "id": "q1",
        "question": "What is photosynthesis?",
        "correct_answer": "Plants converting light to chemical energy",
        "user_answer": "I don't know",
        "is_correct": False,
        "score": 0,
        "type": "short_answer",
    },
    {
        "id": "q2",
        "question": "Is water H2O?",
        "correct_answer": "True",
        "user_answer": "True",
        "is_correct": True,
        "score": 1,
        "type": "true_false",
    },
]

MOCK_CARDS = [
    {"front": "What is photosynthesis?", "back": "Converting light energy to chemical energy in plants.", "category": "Biology"},
    {"front": "What molecule is water?", "back": "H2O", "category": "Chemistry"},
]


@pytest.mark.asyncio
async def test_generate_from_quiz(svc):
    with patch(
        "app.services.flashcard_service.llm_service.generate_json",
        new_callable=AsyncMock,
        return_value=MOCK_CARDS,
    ):
        cards = await svc.generate_from_quiz(SAMPLE_QUESTIONS, num_cards=2)
        assert len(cards) == 2
        assert all("id" in c and "front" in c and "back" in c and "category" in c for c in cards)


@pytest.mark.asyncio
async def test_generate_from_document(svc):
    with patch(
        "app.services.flashcard_service.llm_service.generate_json",
        new_callable=AsyncMock,
        return_value=MOCK_CARDS,
    ):
        cards = await svc.generate_from_document(["chunk one about biology"], num_cards=2)
        assert len(cards) == 2


@pytest.mark.asyncio
async def test_llm_failure_returns_empty(svc):
    with patch(
        "app.services.flashcard_service.llm_service.generate_json",
        new_callable=AsyncMock,
        side_effect=RuntimeError("LLM down"),
    ):
        cards = await svc.generate_from_quiz(SAMPLE_QUESTIONS, num_cards=5)
        assert cards == []


def test_normalize_card_defaults():
    card = _normalize_card({})
    assert card["front"] == ""
    assert card["back"] == ""
    assert card["category"] == "General"
    assert "id" in card


def test_normalize_card_strips_whitespace():
    card = _normalize_card({"front": "  Q?  ", "back": "  A.  ", "category": "  Bio  "})
    assert card["front"] == "Q?"
    assert card["back"] == "A."
    assert card["category"] == "Bio"


@pytest.mark.asyncio
async def test_llm_wrapped_dict_unwrapped(svc):
    """If LLM returns {flashcards: [...]} it should be unwrapped."""
    wrapped = {"flashcards": MOCK_CARDS}
    with patch(
        "app.services.flashcard_service.llm_service.generate_json",
        new_callable=AsyncMock,
        return_value=wrapped,
    ):
        cards = await svc.generate_from_document(["some content"], num_cards=2)
        assert len(cards) == 2


# ── Router integration tests ────────────────────────────────────────────────

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_flashcard_endpoint_quiz_not_found(client):
    resp = await client.post(
        "/api/flashcards/generate",
        json={"source_type": "quiz", "quiz_id": "nonexistent-id", "num_cards": 5},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_flashcard_endpoint_missing_quiz_id(client):
    resp = await client.post(
        "/api/flashcards/generate",
        json={"source_type": "quiz", "num_cards": 5},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_flashcard_endpoint_invalid_source(client):
    resp = await client.post(
        "/api/flashcards/generate",
        json={"source_type": "invalid"},
    )
    assert resp.status_code == 422  # Pydantic validation
