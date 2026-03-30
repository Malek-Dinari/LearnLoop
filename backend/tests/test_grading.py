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
async def test_grade_true_false():
    question = {
        "type": "true_false",
        "question": "The sky is blue.",
        "correct_answer": "True",
        "explanation": "The sky appears blue due to Rayleigh scattering.",
    }
    result = await quiz_service.grade_answer(question, "True")
    assert result["is_correct"] is True
