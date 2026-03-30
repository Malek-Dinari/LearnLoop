import pytest
from app.services.quiz_service import quiz_service


@pytest.mark.asyncio
async def test_generate_topic_questions():
    questions = await quiz_service.generate_questions(
        content="photosynthesis",
        source_type="topic",
        num_questions=2,
        question_types=["mcq"],
    )
    assert len(questions) >= 1
    for q in questions:
        assert "id" in q
        assert "question" in q
        assert "correct_answer" in q
        assert q["type"] in ("mcq", "true_false", "short_answer")


@pytest.mark.asyncio
async def test_generate_document_questions():
    content = (
        "The mitochondria is the powerhouse of the cell. "
        "It produces ATP through cellular respiration. "
        "The process involves the electron transport chain in the inner membrane."
    )
    questions = await quiz_service.generate_questions(
        content=content,
        source_type="document",
        num_questions=2,
        question_types=["mcq", "true_false"],
    )
    assert len(questions) >= 1
