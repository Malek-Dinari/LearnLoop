import asyncio
import logging
import time

from groq import AsyncGroq, APITimeoutError, RateLimitError, BadRequestError, APIError

from app.config import settings
from app.services.llm_service import BaseLLMService, _extract_json, truncate_prompt

logger = logging.getLogger(__name__)


class GroqLLMService(BaseLLMService):
    """LLM service backed by the Groq API (OpenAI-compatible chat completions)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self._api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model
        self._timeout = settings.groq_request_timeout
        if not self._api_key:
            logger.warning(
                "Groq API key not set — all LLM calls will fail. "
                "Set GROQ_API_KEY in your .env file."
            )

    def _client(self) -> AsyncGroq:
        return AsyncGroq(api_key=self._api_key, timeout=self._timeout)

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": truncate_prompt(prompt)})

        last_error: Exception | None = None
        for attempt in range(3):
            t0 = time.monotonic()
            try:
                response = await self._client().chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore[arg-type]
                    temperature=temperature,
                    max_tokens=settings.llm_num_predict_text,
                )
                elapsed = time.monotonic() - t0
                content = response.choices[0].message.content or ""
                logger.info(
                    f"Groq call completed in {elapsed:.2f}s "
                    f"(model={self.model}, chars_out={len(content)})"
                )
                return content
            except RateLimitError as exc:
                logger.warning(f"Groq rate limit (attempt {attempt + 1}/3): {exc}")
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
            except APITimeoutError as exc:
                logger.warning(f"Groq timeout (attempt {attempt + 1}/3): {exc}")
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
            except APIError as exc:
                logger.error(f"Groq API error (attempt {attempt + 1}/3): {exc}")
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(2)
                    continue

        raise last_error  # type: ignore[misc]

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        num_predict: int | None = None,
    ) -> dict | list:
        effective_max_tokens = num_predict or settings.llm_num_predict_json
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": truncate_prompt(prompt)})

        for attempt in range(3):
            t0 = time.monotonic()
            raw = ""
            try:
                # Try JSON mode first — Groq supports it for llama-3.x and mixtral
                response = await self._client().chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore[arg-type]
                    temperature=temperature,
                    max_tokens=effective_max_tokens,
                    response_format={"type": "json_object"},
                )
                elapsed = time.monotonic() - t0
                raw = response.choices[0].message.content or ""
                logger.info(
                    f"Groq JSON call completed in {elapsed:.2f}s "
                    f"(model={self.model}, chars_out={len(raw)})"
                )
            except BadRequestError:
                # Model doesn't support JSON mode — fall back to plain text
                logger.info(
                    f"Groq JSON mode not supported for {self.model}, falling back to text"
                )
                response = await self._client().chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore[arg-type]
                    temperature=temperature,
                    max_tokens=effective_max_tokens,
                )
                elapsed = time.monotonic() - t0
                raw = response.choices[0].message.content or ""
                logger.info(
                    f"Groq text-fallback call completed in {elapsed:.2f}s "
                    f"(model={self.model}, chars_out={len(raw)})"
                )
            except RateLimitError as exc:
                logger.warning(f"Groq rate limit (attempt {attempt + 1}/3): {exc}")
                if attempt < 2:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                raise
            except (APITimeoutError, APIError) as exc:
                logger.warning(f"Groq error (attempt {attempt + 1}/3): {exc}")
                if attempt < 2:
                    await asyncio.sleep(2)
                    continue
                raise

            if len(raw.strip()) < 20:
                logger.warning(
                    f"Suspiciously short Groq response (attempt {attempt + 1}): {raw!r}"
                )

            try:
                return _extract_json(raw)
            except ValueError as exc:
                logger.warning(f"JSON extraction failed (attempt {attempt + 1}/3): {exc}")
                if attempt < 2:
                    messages.append({"role": "assistant", "content": raw})
                    messages.append({
                        "role": "user",
                        "content": (
                            "Your previous response was not valid JSON. "
                            "Respond with ONLY a raw JSON array of objects. "
                            "No markdown, no explanations, no code fences. "
                            'Example format: [{"type":"mcq","question":"...","options":[...],'
                            '"correct_answer":"...","explanation":"...","difficulty":"easy"}]'
                        ),
                    })
                    continue
                raise

        raise RuntimeError("All Groq generate_json attempts exhausted")

    async def health_check(self) -> bool:
        try:
            client = self._client()
            models = await client.models.list()
            available = [m.id for m in models.data]
            ok = self.model in available
            if not ok:
                logger.warning(
                    f"Groq model {self.model!r} not in available models: {available[:10]}"
                )
            return ok
        except Exception as exc:
            logger.warning(f"Groq health check failed: {exc}")
            return False
