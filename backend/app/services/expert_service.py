"""Expert-in-the-Loop service: fetch + format approved corrections.

Used by the quiz generation pipeline to inject few-shot examples of
expert-verified questions into the prompt, raising quality without
fine-tuning.
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import ExpertCorrection
from app.services.quiz_service import extract_topic_keywords

logger = logging.getLogger(__name__)


def _candidate_tags(content: str, source_type: str, topic: str | None) -> set[str]:
    """Build a set of lowercased candidate tags from the request inputs."""
    tags: set[str] = set()
    if topic:
        tags.update(t.strip().lower() for t in topic.replace(",", " ").split() if t.strip())
    snippet = (topic or "")[:200] or content[:200]
    tags.update(k.lower() for k in extract_topic_keywords(snippet, num_words=8))
    return {t for t in tags if t}


async def fetch_relevant_corrections(
    db: AsyncSession,
    content: str,
    source_type: str,
    topic: str | None,
    limit: int = 3,
) -> list[dict]:
    """Return up to `limit` approved corrections whose topic_tags overlap.

    Strategy: pull the most recent `approved=True` corrections, filter in
    Python by tag overlap. JSON queries differ across PG / SQLite so this
    is the portable path.
    """
    candidates = _candidate_tags(content, source_type, topic)
    if not candidates:
        return []

    stmt = (
        select(ExpertCorrection)
        .where(ExpertCorrection.approved.is_(True))
        .order_by(ExpertCorrection.created_at.desc())
        .limit(50)  # small bounded scan
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    matches: list[dict] = []
    for row in rows:
        tags = {str(t).lower() for t in (row.topic_tags or [])}
        if tags & candidates:
            matches.append(row.corrected_question)
            if len(matches) >= limit:
                break
    return matches


def build_few_shot_block(corrections: list[dict[str, Any]]) -> str:
    """Format corrections as a system-prompt addition. Empty if none."""
    if not corrections:
        return ""
    lines = []
    for c in corrections:
        q = str(c.get("question", "")).strip()
        a = str(c.get("correct_answer", "")).strip()
        if q:
            lines.append(f"- Q: {q}\n  A: {a}")
    if not lines:
        return ""
    examples = "\n".join(lines)
    return (
        "\n\nThese expert-approved questions show the style and accuracy "
        "you should match:\n"
        f"{examples}\n"
    )
