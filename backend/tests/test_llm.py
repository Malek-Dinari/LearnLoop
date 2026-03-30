import pytest
from app.services.llm_service import llm_service, _extract_json


@pytest.mark.asyncio
async def test_health_check():
    result = await llm_service.health_check()
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_generate():
    result = await llm_service.generate("Say hello in one word.", temperature=0.3)
    assert isinstance(result, str)
    assert len(result) > 0


def test_extract_json_raw():
    assert _extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced():
    text = '```json\n{"a": 1}\n```'
    assert _extract_json(text) == {"a": 1}


def test_extract_json_with_think():
    text = '<think>reasoning here</think>\n[{"q": "test"}]'
    result = _extract_json(text)
    assert isinstance(result, list)


def test_extract_json_array():
    assert _extract_json('[1, 2, 3]') == [1, 2, 3]
