import pytest
from unittest.mock import AsyncMock, patch
from app.services.quiz_service import QuizService, quiz_service


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


@pytest.mark.asyncio
async def test_generate_batch_partial_failure():
    """If some batches fail, successful batches still return questions."""
    svc = QuizService()

    call_count = 0

    async def mock_generate_json(prompt, system_prompt="", temperature=0.3, **kwargs):
        nonlocal call_count
        call_count += 1
        # Fail on the second call
        if call_count == 2:
            raise RuntimeError("Simulated LLM failure")
        return [
            {
                "type": "mcq",
                "question": f"Question from batch {call_count}?",
                "options": ["A) opt1", "B) opt2", "C) opt3", "D) opt4"],
                "correct_answer": "A) opt1",
                "explanation": "Because opt1.",
                "difficulty": "easy",
            }
        ]

    with patch.object(svc._generate_batch.__self__.__class__, '_generate_batch', wraps=svc._generate_batch):
        with patch('app.services.quiz_service.llm_service') as mock_llm:
            mock_llm.generate_json = AsyncMock(side_effect=mock_generate_json)
            questions = await svc.generate_questions(
                content="test topic",
                source_type="topic",
                num_questions=6,
                question_types=["mcq"],
            )
    # Should get questions from the successful batches, not zero
    assert len(questions) >= 1


@pytest.mark.asyncio
async def test_deduplication():
    """Duplicate questions from different batches should be deduplicated."""
    svc = QuizService()

    duplicate_question = {
        "type": "mcq",
        "question": "What is photosynthesis?",
        "options": ["A) opt1", "B) opt2", "C) opt3", "D) opt4"],
        "correct_answer": "A) opt1",
        "explanation": "It is the process.",
        "difficulty": "easy",
    }

    async def mock_generate_json(prompt, system_prompt="", temperature=0.3, **kwargs):
        return [duplicate_question]

    with patch('app.services.quiz_service.llm_service') as mock_llm:
        mock_llm.generate_json = AsyncMock(side_effect=mock_generate_json)
        questions = await svc.generate_questions(
            content="photosynthesis",
            source_type="topic",
            num_questions=6,
            question_types=["mcq"],
        )

    # Duplicate question text should appear only once
    question_texts = [q["question"].strip().lower() for q in questions]
    assert len(question_texts) == len(set(question_texts))
