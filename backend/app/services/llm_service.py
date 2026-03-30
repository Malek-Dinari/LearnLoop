import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class BaseLLMService(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7) -> str:
        ...

    @abstractmethod
    async def generate_json(self, prompt: str, system_prompt: str = "", temperature: float = 0.3) -> dict | list:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...


def _extract_json(text: str) -> dict | list:
    """Extract JSON from LLM response, stripping markdown fences and /think blocks."""
    # Strip <think>...</think> blocks (Qwen thinking mode)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find JSON array or object in text
    for pattern in [r"\[.*\]", r"\{.*\}"]:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract JSON from response: {text[:500]}")


class OllamaLLMService(BaseLLMService):
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model

    async def _call_ollama(
        self, messages: list[dict], temperature: float = 0.7, think: bool = True
    ) -> str:
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_ctx": 16384},
        }

        # Append /no_think to suppress Qwen's extended reasoning for structured output
        if not think:
            msgs_copy = [m.copy() for m in messages]
            for m in reversed(msgs_copy):
                if m["role"] == "user":
                    m["content"] = m["content"] + " /no_think"
                    break
            payload["messages"] = msgs_copy

        # Retry on 500 (Ollama returns 500 when model is busy or context issues)
        last_error = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=600.0) as client:
                    response = await client.post(
                        f"{self.base_url}/api/chat",
                        json=payload,
                    )
                    if response.status_code == 500:
                        error_text = response.text[:500]
                        logger.warning(f"Ollama 500 (attempt {attempt+1}/3): {error_text}")
                        last_error = httpx.HTTPStatusError(
                            f"Ollama 500: {error_text}",
                            request=response.request,
                            response=response,
                        )
                        if attempt < 2:
                            await asyncio.sleep(3 * (attempt + 1))
                            continue
                        raise last_error
                    response.raise_for_status()
                    data = response.json()
                    return data["message"]["content"]
            except httpx.ReadTimeout:
                logger.warning(f"Ollama timeout (attempt {attempt+1}/3)")
                last_error = httpx.ReadTimeout("Ollama request timed out")
                if attempt < 2:
                    await asyncio.sleep(2)
                    continue
                raise last_error
        raise last_error  # type: ignore[misc]

    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        raw = await self._call_ollama(messages, temperature, think=True)
        # Strip thinking blocks from output
        return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    async def generate_json(self, prompt: str, system_prompt: str = "", temperature: float = 0.3) -> dict | list:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(3):
            # Disable thinking for JSON generation — much faster
            raw = await self._call_ollama(messages, temperature, think=False)
            try:
                return _extract_json(raw)
            except ValueError:
                if attempt < 2:
                    messages.append({"role": "assistant", "content": raw})
                    messages.append({
                        "role": "user",
                        "content": (
                            "Your previous response was not valid JSON. "
                            "Respond with ONLY raw JSON. No markdown, no explanation, no code fences."
                        ),
                    })
                    continue
                raise

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                models = resp.json().get("models", [])
                return any(m["name"].startswith(self.model.split(":")[0]) for m in models)
        except Exception:
            return False


# Singleton instance
llm_service = OllamaLLMService()
