"""Unit tests for ChatService — coaching and study chat."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.chat_service import ChatService, MAX_CONVERSATION_MESSAGES


@pytest.fixture
def chat():
    return ChatService()


SAMPLE_QUESTION = {
    "question": "What is photosynthesis?",
    "correct_answer": "The process by which plants convert light energy to chemical energy",
    "source_chunk": None,
}


@pytest.mark.asyncio
async def test_coach_basic(chat):
    with patch(
        "app.services.chat_service.llm_service.generate",
        new_callable=AsyncMock,
        return_value="Think about how plants use sunlight.",
    ) as mock_gen:
        result = await chat.coach(
            question=SAMPLE_QUESTION,
            user_answer="I don't know",
            conversation=[],
            user_message="Can you help?",
        )
        assert result == "Think about how plants use sunlight."
        mock_gen.assert_called_once()
        # Verify prompt contains the question
        prompt_arg = mock_gen.call_args[0][0]
        assert "photosynthesis" in prompt_arg.lower()


@pytest.mark.asyncio
async def test_coach_long_conversation_truncated(chat):
    long_convo = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
        for i in range(50)
    ]

    with patch(
        "app.services.chat_service.llm_service.generate",
        new_callable=AsyncMock,
        return_value="Here's a hint.",
    ) as mock_gen:
        await chat.coach(
            question=SAMPLE_QUESTION,
            user_answer="dunno",
            conversation=long_convo,
            user_message="Help",
        )
        prompt_arg = mock_gen.call_args[0][0]
        # Should only contain last MAX_CONVERSATION_MESSAGES messages
        assert "Message 0" not in prompt_arg
        assert f"Message {50 - 1}" in prompt_arg


@pytest.mark.asyncio
async def test_coach_llm_failure_returns_fallback(chat):
    with patch(
        "app.services.chat_service.llm_service.generate",
        new_callable=AsyncMock,
        side_effect=RuntimeError("LLM unavailable"),
    ):
        result = await chat.coach(
            question=SAMPLE_QUESTION,
            user_answer="test",
            conversation=[],
            user_message="Help me",
        )
        assert "trouble" in result.lower()


# ── Study chat tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_study_chat_basic(chat):
    with patch(
        "app.services.chat_service.llm_service.generate",
        new_callable=AsyncMock,
        return_value="Here's an explanation.",
    ) as mock_gen:
        result = await chat.study_chat(
            context="Machine Learning",
            conversation=[],
            user_message="What is gradient descent?",
        )
        assert result == "Here's an explanation."
        mock_gen.assert_called_once()


@pytest.mark.asyncio
async def test_study_chat_with_quiz_context(chat):
    quiz_summary = {
        "score": 3,
        "total": 10,
        "percentage": 30.0,
        "weak_areas": ["Photosynthesis", "Cell division"],
    }
    with patch(
        "app.services.chat_service.llm_service.generate",
        new_callable=AsyncMock,
        return_value="Let's work on those weak areas.",
    ) as mock_gen:
        await chat.study_chat(
            context="Biology",
            conversation=[],
            user_message="What should I study?",
            quiz_summary=quiz_summary,
        )
        system_arg = mock_gen.call_args[0][1]
        assert "30" in system_arg or "3/10" in system_arg or "Photosynthesis" in mock_gen.call_args[0][0]


@pytest.mark.asyncio
async def test_study_chat_truncation(chat):
    long_convo = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"Msg {i}"}
        for i in range(40)
    ]
    with patch(
        "app.services.chat_service.llm_service.generate",
        new_callable=AsyncMock,
        return_value="OK",
    ) as mock_gen:
        await chat.study_chat(
            context="",
            conversation=long_convo,
            user_message="Continue",
        )
        prompt = mock_gen.call_args[0][0]
        assert "Msg 0" not in prompt
        assert "Msg 39" in prompt


@pytest.mark.asyncio
async def test_study_chat_llm_failure(chat):
    with patch(
        "app.services.chat_service.llm_service.generate",
        new_callable=AsyncMock,
        side_effect=RuntimeError("LLM down"),
    ):
        result = await chat.study_chat(
            context="",
            conversation=[],
            user_message="help",
        )
        assert "trouble" in result.lower()
