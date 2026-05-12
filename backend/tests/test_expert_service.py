"""Pure-logic + DB-fixture tests for expert_service."""

import uuid

import pytest

from app.db_models import ExpertCorrection, User
from app.services.auth_service import hash_password
from app.services.expert_service import (
    build_few_shot_block,
    fetch_relevant_corrections,
)


def test_build_few_shot_block_empty():
    assert build_few_shot_block([]) == ""


def test_build_few_shot_block_formats_each_correction():
    block = build_few_shot_block([
        {"question": "What is X?", "correct_answer": "A"},
        {"question": "Why Y?", "correct_answer": "B"},
    ])
    assert "expert-approved" in block.lower()
    assert "What is X?" in block
    assert "Why Y?" in block
    assert "A" in block and "B" in block


def test_build_few_shot_block_skips_empty_questions():
    block = build_few_shot_block([{"question": "", "correct_answer": "A"}])
    assert block == ""


@pytest.mark.asyncio
async def test_fetch_filters_unapproved(db):
    expert = User(
        id=uuid.uuid4(),
        email="x@test.com",
        password_hash=hash_password("longpassword"),
        role="expert",
    )
    db.add(expert)
    await db.flush()

    db.add(ExpertCorrection(
        id=uuid.uuid4(),
        original_question=None,
        corrected_question={"question": "approved Q", "correct_answer": "A"},
        topic_tags=["photosynthesis"],
        expert_id=expert.id,
        approved=True,
    ))
    db.add(ExpertCorrection(
        id=uuid.uuid4(),
        original_question=None,
        corrected_question={"question": "pending Q", "correct_answer": "B"},
        topic_tags=["photosynthesis"],
        expert_id=expert.id,
        approved=False,
    ))
    await db.flush()

    matches = await fetch_relevant_corrections(
        db, content="photosynthesis", source_type="topic", topic="photosynthesis", limit=5
    )
    assert len(matches) == 1
    assert matches[0]["question"] == "approved Q"


@pytest.mark.asyncio
async def test_fetch_filters_by_tag_overlap(db):
    expert = User(
        id=uuid.uuid4(),
        email="y@test.com",
        password_hash=hash_password("longpassword"),
        role="expert",
    )
    db.add(expert)
    await db.flush()

    db.add(ExpertCorrection(
        id=uuid.uuid4(),
        original_question=None,
        corrected_question={"question": "X", "correct_answer": "A"},
        topic_tags=["photosynthesis"],
        expert_id=expert.id,
        approved=True,
    ))
    db.add(ExpertCorrection(
        id=uuid.uuid4(),
        original_question=None,
        corrected_question={"question": "Y", "correct_answer": "B"},
        topic_tags=["chemistry"],
        expert_id=expert.id,
        approved=True,
    ))
    await db.flush()

    matches = await fetch_relevant_corrections(
        db, content="photosynthesis", source_type="topic", topic="photosynthesis", limit=5
    )
    assert len(matches) == 1
    assert matches[0]["question"] == "X"


@pytest.mark.asyncio
async def test_fetch_respects_limit(db):
    expert = User(
        id=uuid.uuid4(),
        email="z@test.com",
        password_hash=hash_password("longpassword"),
        role="expert",
    )
    db.add(expert)
    await db.flush()

    for i in range(5):
        db.add(ExpertCorrection(
            id=uuid.uuid4(),
            original_question=None,
            corrected_question={"question": f"Q{i}", "correct_answer": "A"},
            topic_tags=["photosynthesis"],
            expert_id=expert.id,
            approved=True,
        ))
    await db.flush()

    matches = await fetch_relevant_corrections(
        db, content="photosynthesis", source_type="topic", topic="photosynthesis", limit=2
    )
    assert len(matches) == 2
