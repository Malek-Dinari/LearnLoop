import asyncio
import json
import logging
import re
import time
from abc import ABC, abstractmethod

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class BaseLLMService(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7) -> str:
        ...

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        num_predict: int | None = None,
    ) -> dict | list:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...


def truncate_prompt(text: str, max_chars: int | None = None) -> str:
    """Truncate prompt to max_chars at a sentence boundary. Logs a warning when truncation occurs."""
    limit = max_chars if max_chars is not None else settings.llm_max_prompt_chars
    if len(text) <= limit:
        return text
    truncated = text[:limit]
    last_period = truncated.rfind(".")
    if last_period > int(limit * 0.8):
        truncated = truncated[:last_period + 1]
    logger.warning(f"Prompt truncated from {len(text)} to {len(truncated)} chars")
    return truncated + "\n[...content truncated for length...]"


def _extract_json(text: str) -> dict | list:
    """Extract JSON from LLM response, stripping markdown fences and think blocks."""
    # Strip <think>...</think> blocks (Qwen thinking mode)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = text.strip()

    if not text:
        raise ValueError("LLM returned empty response after stripping think blocks")

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

    # Search for JSON array or object in text (handles preamble like "Here is the JSON:")
    # Try array first (expected for question batches), then object
    for pattern in [r"\[.*\]", r"\{.*\}"]:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            candidate = match.group()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # Fix trailing commas (common small-model output issue)
                fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
                try:
                    return json.loads(fixed)
                except json.JSONDecodeError:
                    continue

    raise ValueError(f"Could not extract JSON from response (len={len(text)}): {text[:300]!r}")


class OllamaLLMService(BaseLLMService):
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model

    async def _call_ollama(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        think: bool = True,
        num_predict: int | None = None,
    ) -> str:
        options: dict = {
            "temperature": temperature,
            "num_ctx": settings.llm_num_ctx,   # was hardcoded 16384
        }
        if num_predict is not None:
            options["num_predict"] = num_predict

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": options,
        }

        # Append /no_think to suppress Qwen's extended reasoning for structured output
        if not think:
            msgs_copy = [m.copy() for m in messages]
            for m in reversed(msgs_copy):
                if m["role"] == "user":
                    m["content"] = m["content"] + " /no_think"
                    break
            payload["messages"] = msgs_copy

        last_error = None
        for attempt in range(3):
            t0 = time.monotonic()
            try:
                async with httpx.AsyncClient(timeout=settings.llm_request_timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/api/chat",
                        json=payload,
                    )
                    elapsed = time.monotonic() - t0
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
                    content = data["message"]["content"]
                    logger.info(
                        f"LLM call completed in {elapsed:.2f}s "
                        f"(model={self.model}, num_predict={num_predict}, "
                        f"num_ctx={settings.llm_num_ctx}, chars_out={len(content)})"
                    )
                    return content
            except httpx.ReadTimeout:
                elapsed = time.monotonic() - t0
                logger.warning(f"Ollama timeout after {elapsed:.1f}s (attempt {attempt+1}/3)")
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
        messages.append({"role": "user", "content": truncate_prompt(prompt)})
        raw = await self._call_ollama(
            messages, temperature, think=True, num_predict=settings.llm_num_predict_text
        )
        return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        num_predict: int | None = None,
    ) -> dict | list:
        """
        Generate a JSON response from the LLM.
        num_predict overrides the config default — callers that know they need more tokens
        (e.g. batches of 3 questions) should pass an explicit value.
        """
        effective_predict = num_predict if num_predict is not None else settings.llm_num_predict_json
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": truncate_prompt(prompt)})

        for attempt in range(3):
            raw = await self._call_ollama(
                messages, temperature, think=False, num_predict=effective_predict
            )
            # Log the raw response when it's short/suspicious — helps diagnose cut-offs
            if len(raw.strip()) < 20:
                logger.warning(f"Suspiciously short LLM response (attempt {attempt+1}): {raw!r}")
            try:
                return _extract_json(raw)
            except ValueError as exc:
                logger.warning(f"JSON extraction failed (attempt {attempt+1}/3): {exc}")
                if attempt < 2:
                    messages.append({"role": "assistant", "content": raw})
                    messages.append({
                        "role": "user",
                        "content": (
                            "Your previous response was not valid JSON. "
                            "Respond with ONLY a raw JSON array of objects. "
                            "No markdown, no explanations, no code fences. "
                            'Example format: [{"type":"mcq","question":"...","options":[...],"correct_answer":"...","explanation":"...","difficulty":"easy"}]'
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
