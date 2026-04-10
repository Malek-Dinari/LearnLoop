import logging
import uuid

from app.prompts.flashcards import (
    FLASHCARD_SYSTEM,
    FLASHCARD_FROM_QUIZ_USER,
    FLASHCARD_FROM_DOCUMENT_USER,
)
from app.services.llm_service import llm_service, truncate_prompt
from app.services.cache_service import cache, make_cache_key

logger = logging.getLogger(__name__)


def _normalize_card(card: dict) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "front": str(card.get("front") or "").strip(),
        "back": str(card.get("back") or "").strip(),
        "category": str(card.get("category") or "General").strip(),
    }


def _format_question(q: dict) -> str:
    ans = q.get("user_answer", "") or ""
    correct = q.get("correct_answer", "") or ""
    is_correct = q.get("is_correct", True)
    marker = "✓" if is_correct else "✗"
    return f"{marker} Q: {q.get('question', '')} | Correct: {correct} | Student answered: {ans}"


class FlashcardService:
    async def generate_from_quiz(
        self,
        questions_with_results: list[dict],
        num_cards: int = 10,
    ) -> list[dict]:
        import hashlib, json

        cache_key = make_cache_key(
            "flashcards_quiz",
            q_hash=hashlib.sha256(json.dumps(questions_with_results, sort_keys=True).encode()).hexdigest()[:16],
            num_cards=num_cards,
        )
        cached = await cache.get(cache_key)
        if cached is not None:
            logger.info("Flashcard cache HIT (quiz)")
            return cached

        wrong = [q for q in questions_with_results if not q.get("is_correct", True)]
        all_lines = "\n".join(_format_question(q) for q in questions_with_results)
        wrong_lines = "\n".join(_format_question(q) for q in wrong) or "(none — all correct!)"

        prompt = FLASHCARD_FROM_QUIZ_USER.format(
            num_cards=num_cards,
            wrong_questions=truncate_prompt(wrong_lines, max_chars=3000),
            all_questions=truncate_prompt(all_lines, max_chars=3000),
        )

        cards = await self._call_llm(prompt, num_cards)
        await cache.set(cache_key, cards, ttl=3600)
        return cards

    async def generate_from_document(
        self,
        chunks: list[str],
        num_cards: int = 10,
    ) -> list[dict]:
        import hashlib

        content = "\n\n".join(chunks)
        cache_key = make_cache_key(
            "flashcards_doc",
            c_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
            num_cards=num_cards,
        )
        cached = await cache.get(cache_key)
        if cached is not None:
            logger.info("Flashcard cache HIT (document)")
            return cached

        safe_content = truncate_prompt(content, max_chars=8000)
        prompt = FLASHCARD_FROM_DOCUMENT_USER.format(
            num_cards=num_cards,
            content=safe_content,
        )

        cards = await self._call_llm(prompt, num_cards)
        await cache.set(cache_key, cards, ttl=3600)
        return cards

    async def _call_llm(self, prompt: str, num_cards: int) -> list[dict]:
        try:
            raw = await llm_service.generate_json(prompt, FLASHCARD_SYSTEM, temperature=0.4)
        except Exception:
            logger.exception("Flashcard LLM call failed")
            return []

        if isinstance(raw, dict):
            for key in ("flashcards", "cards", "items", "data"):
                if key in raw and isinstance(raw[key], list):
                    raw = raw[key]
                    break
            else:
                for val in raw.values():
                    if isinstance(val, list):
                        raw = val
                        break
                else:
                    logger.warning("Flashcard LLM returned dict with no list: %s", list(raw.keys()))
                    return []

        if not isinstance(raw, list):
            logger.warning("Flashcard LLM returned non-list: %s", type(raw))
            return []

        cards = [_normalize_card(c) for c in raw[:num_cards] if isinstance(c, dict)]
        # Drop cards with empty front or back
        cards = [c for c in cards if c["front"] and c["back"]]
        logger.info("Generated %d flashcards", len(cards))
        return cards


flashcard_service = FlashcardService()
