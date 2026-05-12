"""Auth + quiz integration: anonymous + authenticated paths."""

from unittest.mock import AsyncMock, patch
import uuid

import pytest
from sqlalchemy import select


SAMPLE_QUESTIONS = [
    {
        "id": str(uuid.uuid4()),
        "type": "mcq",
        "question": "What is photosynthesis?",
        "options": ["Light into chemical energy", "Heat into work", "Mass into volume", "Sound into noise"],
        "correct_answer": "Light into chemical energy",
        "explanation": "Photosynthesis converts light energy.",
        "difficulty": "easy",
        "expert_verified": False,
    }
]


@pytest.mark.asyncio
async def test_quiz_anonymous_still_works(auth_client):
    with patch(
        "app.services.quiz_service.quiz_service.generate_questions",
        new=AsyncMock(return_value=SAMPLE_QUESTIONS),
    ):
        resp = await auth_client.post(
            "/api/quiz/generate",
            json={"source_type": "topic", "topic": "biology", "num_questions": 1},
        )
    assert resp.status_code == 200, resp.text
    assert "quiz_id" in resp.json()


@pytest.mark.asyncio
async def test_quiz_authenticated_associates_user(auth_app, auth_client, make_user):
    _, session_factory = auth_app
    user = await make_user(email="quiz-owner@test.com")

    with patch(
        "app.services.quiz_service.quiz_service.generate_questions",
        new=AsyncMock(return_value=SAMPLE_QUESTIONS),
    ):
        resp = await auth_client.post(
            "/api/quiz/generate",
            json={"source_type": "topic", "topic": "biology", "num_questions": 1},
            headers=user["headers"],
        )
    assert resp.status_code == 200, resp.text
    quiz_id = resp.json()["quiz_id"]

    from app.db_models import Quiz
    async with session_factory() as session:
        row = await session.scalar(select(Quiz).where(Quiz.id == uuid.UUID(quiz_id)))
        assert row is not None
        assert row.user_id is not None
        assert str(row.user_id) == user["id"]


@pytest.mark.asyncio
async def test_invalid_token_treated_as_anonymous(auth_app, auth_client):
    _, session_factory = auth_app

    with patch(
        "app.services.quiz_service.quiz_service.generate_questions",
        new=AsyncMock(return_value=SAMPLE_QUESTIONS),
    ):
        resp = await auth_client.post(
            "/api/quiz/generate",
            json={"source_type": "topic", "topic": "biology", "num_questions": 1},
            headers={"Authorization": "Bearer garbage-token"},
        )
    assert resp.status_code == 200
    quiz_id = resp.json()["quiz_id"]

    from app.db_models import Quiz
    async with session_factory() as session:
        row = await session.scalar(select(Quiz).where(Quiz.id == uuid.UUID(quiz_id)))
        assert row is not None
        assert row.user_id is None
