"""Cross-feature: approved corrections must be injected into quiz prompts."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.db_models import ExpertCorrection, User
from app.services.auth_service import hash_password
from app.services.quiz_service import quiz_service


def _llm_returns_one_question():
    return AsyncMock(return_value=[
        {
            "type": "mcq",
            "question": "Generated question",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "explanation": "Because.",
            "difficulty": "medium",
        }
    ])


@pytest.mark.asyncio
async def test_approved_correction_injected_for_matching_topic(db):
    expert = User(
        id=uuid.uuid4(),
        email="e@test.com",
        password_hash=hash_password("longpassword"),
        role="expert",
    )
    db.add(expert)
    db.add(ExpertCorrection(
        id=uuid.uuid4(),
        original_question=None,
        corrected_question={
            "question": "What converts light to chemical energy?",
            "correct_answer": "Photosynthesis",
        },
        topic_tags=["photosynthesis"],
        expert_id=expert.id,
        approved=True,
    ))
    await db.flush()

    captured = {}

    async def fake_generate_json(user, system, **kw):
        captured["system"] = system
        captured["user"] = user
        return [
            {
                "type": "mcq",
                "question": "Generated Q",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "explanation": "x",
                "difficulty": "easy",
            }
        ]

    with patch(
        "app.services.quiz_service.llm_service.generate_json",
        side_effect=fake_generate_json,
    ):
        questions = await quiz_service._generate_batch(
            content="photosynthesis",
            source_type="topic",
            batch_size=1,
            question_types=["mcq"],
            batch_index=0,
            db=db,
            topic_hint="photosynthesis",
        )

    assert "expert-approved" in captured["system"].lower()
    assert "What converts light" in captured["system"]
    assert questions and questions[0]["expert_verified"] is True


@pytest.mark.asyncio
async def test_no_injection_when_topic_unrelated(db):
    expert = User(
        id=uuid.uuid4(),
        email="e2@test.com",
        password_hash=hash_password("longpassword"),
        role="expert",
    )
    db.add(expert)
    db.add(ExpertCorrection(
        id=uuid.uuid4(),
        original_question=None,
        corrected_question={
            "question": "Photosynthesis Q",
            "correct_answer": "A",
        },
        topic_tags=["photosynthesis"],
        expert_id=expert.id,
        approved=True,
    ))
    await db.flush()

    captured = {}

    async def fake_generate_json(user, system, **kw):
        captured["system"] = system
        return [
            {
                "type": "mcq",
                "question": "Q",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "explanation": "x",
                "difficulty": "easy",
            }
        ]

    with patch(
        "app.services.quiz_service.llm_service.generate_json",
        side_effect=fake_generate_json,
    ):
        questions = await quiz_service._generate_batch(
            content="quantum mechanics",
            source_type="topic",
            batch_size=1,
            question_types=["mcq"],
            batch_index=0,
            db=db,
            topic_hint="quantum mechanics",
        )

    assert "expert-approved" not in captured["system"].lower()
    assert questions and questions[0]["expert_verified"] is False


@pytest.mark.asyncio
async def test_unapproved_corrections_not_injected(db):
    expert = User(
        id=uuid.uuid4(),
        email="e3@test.com",
        password_hash=hash_password("longpassword"),
        role="expert",
    )
    db.add(expert)
    db.add(ExpertCorrection(
        id=uuid.uuid4(),
        original_question=None,
        corrected_question={"question": "PENDING", "correct_answer": "A"},
        topic_tags=["photosynthesis"],
        expert_id=expert.id,
        approved=False,
    ))
    await db.flush()

    captured = {}

    async def fake_generate_json(user, system, **kw):
        captured["system"] = system
        return [
            {
                "type": "mcq",
                "question": "Q",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "explanation": "x",
                "difficulty": "easy",
            }
        ]

    with patch(
        "app.services.quiz_service.llm_service.generate_json",
        side_effect=fake_generate_json,
    ):
        questions = await quiz_service._generate_batch(
            content="photosynthesis",
            source_type="topic",
            batch_size=1,
            question_types=["mcq"],
            batch_index=0,
            db=db,
            topic_hint="photosynthesis",
        )

    assert "PENDING" not in captured["system"]
    assert questions and questions[0]["expert_verified"] is False
