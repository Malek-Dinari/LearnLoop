import pytest
from app.services.quiz_service import quiz_service


@pytest.mark.asyncio
async def test_grade_mcq_correct():
    question = {
        "type": "mcq",
        "question": "What is 2+2?",
        "correct_answer": "4",
        "explanation": "Basic arithmetic.",
    }
    result = await quiz_service.grade_answer(question, "4")
    assert result["is_correct"] is True
    assert result["score"] == 1.0


@pytest.mark.asyncio
async def test_grade_mcq_incorrect():
    question = {
        "type": "mcq",
        "question": "What is 2+2?",
        "correct_answer": "4",
        "explanation": "Basic arithmetic.",
    }
    result = await quiz_service.grade_answer(question, "5")
    assert result["is_correct"] is False
    assert result["score"] == 0.0


@pytest.mark.asyncio
async def test_grade_mcq_whitespace():
    """Whitespace around answer should not affect grading."""
    question = {
        "type": "mcq",
        "question": "What is 2+2?",
        "correct_answer": "4",
        "explanation": "Basic arithmetic.",
    }
    result = await quiz_service.grade_answer(question, "  4  ")
    assert result["is_correct"] is True


@pytest.mark.asyncio
async def test_grade_mcq_no_false_positive():
    """'4' must NOT match '14' — the old substring bug."""
    question = {
        "type": "mcq",
        "question": "What is 7+7?",
        "correct_answer": "14",
        "explanation": "Basic arithmetic.",
    }
    result = await quiz_service.grade_answer(question, "4")
    assert result["is_correct"] is False


@pytest.mark.asyncio
async def test_grade_mcq_option_prefix():
    """'A) Photosynthesis' should match 'photosynthesis'."""
    question = {
        "type": "mcq",
        "question": "What process do plants use?",
        "correct_answer": "Photosynthesis",
        "explanation": "Plants convert light energy.",
    }
    result = await quiz_service.grade_answer(question, "A) Photosynthesis")
    assert result["is_correct"] is True


@pytest.mark.asyncio
async def test_grade_mcq_numbered_prefix():
    """'2) True' should match 'True'."""
    question = {
        "type": "mcq",
        "question": "Is the sky blue?",
        "correct_answer": "True",
        "explanation": "Yes it is.",
    }
    result = await quiz_service.grade_answer(question, "2) True")
    assert result["is_correct"] is True


@pytest.mark.asyncio
async def test_grade_true_false():
    question = {
        "type": "true_false",
        "question": "The sky is blue.",
        "correct_answer": "True",
        "explanation": "The sky appears blue due to Rayleigh scattering.",
    }
    result = await quiz_service.grade_answer(question, "True")
    assert result["is_correct"] is True
