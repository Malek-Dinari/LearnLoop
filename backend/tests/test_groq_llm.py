"""Tests for GroqLLMService — all mocked, no API key required."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.groq_llm_service import GroqLLMService


def _mock_choice(content: str) -> MagicMock:
    """Build a mock ChatCompletion response."""
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.fixture
def service() -> GroqLLMService:
    return GroqLLMService(api_key="test-key", model="llama-3.3-70b-versatile")


@pytest.mark.asyncio
async def test_generate(service: GroqLLMService) -> None:
    mock_response = _mock_choice("Hello! How can I help?")
    with patch.object(service, "_client") as mock_client_fn:
        client = AsyncMock()
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_fn.return_value = client

        result = await service.generate("Say hello")
        assert result == "Hello! How can I help?"
        client.chat.completions.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_json_with_json_mode(service: GroqLLMService) -> None:
    data = [{"type": "mcq", "question": "What is 2+2?", "correct_answer": "4"}]
    mock_response = _mock_choice(json.dumps(data))
    with patch.object(service, "_client") as mock_client_fn:
        client = AsyncMock()
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_fn.return_value = client

        result = await service.generate_json("Generate a quiz question")
        assert isinstance(result, list)
        assert result[0]["question"] == "What is 2+2?"

        # Verify JSON mode was requested
        call_kwargs = client.chat.completions.create.call_args
        assert call_kwargs.kwargs.get("response_format") == {"type": "json_object"}


@pytest.mark.asyncio
async def test_generate_json_fallback_on_bad_request(service: GroqLLMService) -> None:
    """When model doesn't support JSON mode, falls back to text + extraction."""
    from groq import BadRequestError

    data = [{"type": "mcq", "question": "Test?", "correct_answer": "Yes"}]
    mock_text_response = _mock_choice(json.dumps(data))

    with patch.object(service, "_client") as mock_client_fn:
        client = AsyncMock()

        # First call raises BadRequestError (JSON mode not supported)
        # Second call returns plain text
        mock_request = MagicMock()
        bad_req = BadRequestError(
            message="JSON mode not supported",
            response=MagicMock(status_code=400),
            body=None,
        )
        client.chat.completions.create = AsyncMock(side_effect=[bad_req, mock_text_response])
        mock_client_fn.return_value = client

        result = await service.generate_json("Generate a quiz question")
        assert isinstance(result, list)
        assert result[0]["question"] == "Test?"
        assert client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_generate_json_extracts_from_markdown(service: GroqLLMService) -> None:
    """JSON wrapped in markdown fences is still extracted."""
    data = [{"type": "mcq", "question": "Q?", "correct_answer": "A"}]
    wrapped = f"```json\n{json.dumps(data)}\n```"
    mock_response = _mock_choice(wrapped)

    with patch.object(service, "_client") as mock_client_fn:
        client = AsyncMock()
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_fn.return_value = client

        result = await service.generate_json("Generate a quiz question")
        assert isinstance(result, list)
        assert result[0]["question"] == "Q?"


@pytest.mark.asyncio
async def test_health_check_success(service: GroqLLMService) -> None:
    model = MagicMock()
    model.id = "llama-3.3-70b-versatile"
    models_list = MagicMock()
    models_list.data = [model]

    with patch.object(service, "_client") as mock_client_fn:
        client = AsyncMock()
        client.models.list = AsyncMock(return_value=models_list)
        mock_client_fn.return_value = client

        assert await service.health_check() is True


@pytest.mark.asyncio
async def test_health_check_failure(service: GroqLLMService) -> None:
    with patch.object(service, "_client") as mock_client_fn:
        client = AsyncMock()
        client.models.list = AsyncMock(side_effect=Exception("connection refused"))
        mock_client_fn.return_value = client

        assert await service.health_check() is False


@pytest.mark.asyncio
async def test_health_check_model_not_found(service: GroqLLMService) -> None:
    model = MagicMock()
    model.id = "some-other-model"
    models_list = MagicMock()
    models_list.data = [model]

    with patch.object(service, "_client") as mock_client_fn:
        client = AsyncMock()
        client.models.list = AsyncMock(return_value=models_list)
        mock_client_fn.return_value = client

        assert await service.health_check() is False
