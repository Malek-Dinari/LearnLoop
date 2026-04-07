import asyncio
import hashlib
import logging
import uuid
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
from app.prompts.question_gen import (
    DOCUMENT_QUESTION_SYSTEM,
    DOCUMENT_QUESTION_USER,
    TOPIC_QUESTION_SYSTEM,
    TOPIC_QUESTION_USER,
)
from app.prompts.grading import GRADING_SYSTEM, GRADING_USER, SUMMARY_SYSTEM, SUMMARY_USER
from app.services.llm_service import llm_service, truncate_prompt
from app.services.cache_service import cache, make_cache_key

logger = logging.getLogger(__name__)


def _question_types_description(types: list[str]) -> str:
    mapping = {
        "mcq": "Multiple Choice (4 options, one correct)",
        "true_false": "True/False",
        "short_answer": "Short Answer",
    }
    return ", ".join(mapping.get(t, t) for t in types)


def _normalize_question(q: dict, source_type: str, content: str) -> dict:
    """Validate and normalize a raw question dict from the LLM."""
    q_type = q.get("type", "mcq")
    if q_type not in ["mcq", "true_false", "short_answer"]:
        q_type = "mcq"

    question = {
        "id": str(uuid.uuid4()),
        "type": q_type,
        "question": q.get("question", ""),
        "options": q.get("options"),
        "correct_answer": str(q.get("correct_answer", "")),
        "explanation": q.get("explanation", ""),
        "source_chunk": content[:500] if source_type == "document" else None,
        "difficulty": q.get("difficulty", "medium"),
    }

    if q_type == "true_false" and not question["options"]:
        question["options"] = ["True", "False"]

    if q_type == "mcq" and not question["options"]:
        question["type"] = "short_answer"

    return question


class QuizService:
    def __init__(self):
        # quiz_id -> {questions, answers}
        self.quizzes: dict[str, dict] = {}

    async def _generate_batch(
        self,
        content: str,
        source_type: str,
        batch_size: int,
        question_types: list[str],
        batch_index: int,
    ) -> list[dict]:
        """Generate a single batch of questions. Returns [] on failure."""
        types_desc = _question_types_description(question_types)

        try:
            if source_type == "topic":
                system = TOPIC_QUESTION_SYSTEM
                safe_content = truncate_prompt(content, max_chars=500).replace("{", "{{").replace("}", "}}")
                user = TOPIC_QUESTION_USER.format(
                    num_questions=batch_size,
                    topic=safe_content,
                    question_types_description=types_desc,
                )
            else:
                system = DOCUMENT_QUESTION_SYSTEM
                safe_content = truncate_prompt(content).replace("{", "{{").replace("}", "}}")
                user = DOCUMENT_QUESTION_USER.format(
                    num_questions=batch_size,
                    content=safe_content,
                    question_types_description=types_desc,
                )

            # Scale output tokens with batch size.
            # qwen3:1.7b generates ~2 chars/token; a verbose MCQ response is ~1600-2000 chars
            # = ~800-1000 tokens. Use 1500 minimum + 800 per extra question beyond the first.
            batch_num_predict = max(1500, 700 + batch_size * 800)
            raw = await llm_service.generate_json(
                user, system, temperature=0.3, num_predict=batch_num_predict
            )

            # Unwrap if the model returned {"questions": [...]} or any other dict-wrapping
            if isinstance(raw, dict):
                # Try common wrapper keys first
                for key in ("questions", "quiz", "items", "data", "results"):
                    if key in raw and isinstance(raw[key], list):
                        logger.debug(f"Batch {batch_index}: unwrapped dict key '{key}'")
                        raw = raw[key]
                        break
                else:
                    # Fall back: take the first list value found
                    for val in raw.values():
                        if isinstance(val, list):
                            raw = val
                            break
                    else:
                        logger.warning(
                            f"Batch {batch_index}: LLM returned dict with no list values: "
                            f"{list(raw.keys())}"
                        )
                        return []

            if not isinstance(raw, list):
                logger.warning(f"Batch {batch_index}: LLM returned non-list, got {type(raw)}")
                return []

            # Filter out any non-dict items (model sometimes returns string arrays on retry)
            dict_items = [q for q in raw[:batch_size] if isinstance(q, dict)]
            if len(dict_items) < len(raw[:batch_size]):
                logger.warning(
                    f"Batch {batch_index}: filtered {len(raw[:batch_size]) - len(dict_items)} "
                    f"non-dict items from LLM response"
                )
            questions = [_normalize_question(q, source_type, content) for q in dict_items]
            logger.info(f"Batch {batch_index}: generated {len(questions)} questions")
            return questions

        except Exception as exc:
            logger.warning(f"Batch {batch_index} failed: {exc}")
            return []

    async def generate_questions(
        self,
        content: str,
        source_type: str,
        num_questions: int = 10,
        question_types: list[str] | None = None,
    ) -> list[dict]:
        if question_types is None:
            question_types = ["mcq", "true_false", "short_answer"]

        # Check cache first
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        cache_key = make_cache_key(
            "quiz",
            content_hash=content_hash,
            num_questions=num_questions,
            question_types=sorted(question_types),
            source_type=source_type,
        )
        cached = await cache.get(cache_key)
        if cached is not None:
            logger.info(f"Cache HIT — returning {len(cached)} cached questions")
            return cached

        # Build batch plan: chunks of batch_size, last batch gets the remainder
        batch_size = settings.quiz_batch_size
        batches = []
        remaining = num_questions
        while remaining > 0:
            size = min(batch_size, remaining)
            batches.append(size)
            remaining -= size

        logger.info(f"Generating {num_questions} questions in {len(batches)} batches: {batches}")

        # Run batches in parallel when OLLAMA_NUM_PARALLEL > 1 allows it.
        # Each batch is an independent LLM call; asyncio.gather fires them concurrently.
        # With OLLAMA_NUM_PARALLEL=1 (default) Ollama still queues them serially —
        # safe but no faster. Set OLLAMA_NUM_PARALLEL=2 or 3 in your shell before
        # `ollama serve` to actually parallelize (qwen3:1.7b fits 2-3x in 4GB VRAM).
        results = await asyncio.gather(
            *[self._generate_batch(content, source_type, size, question_types, i)
              for i, size in enumerate(batches)],
            return_exceptions=True,
        )
        all_questions: list[dict] = []
        for r in results:
            if isinstance(r, list):
                all_questions.extend(r)
            else:
                logger.warning(f"A batch raised an exception: {r}")

        if not all_questions:
            raise RuntimeError("All question generation batches failed. Check Ollama connectivity.")

        # Deduplicate by question text
        seen: set[str] = set()
        unique: list[dict] = []
        for q in all_questions:
            key = q["question"].strip().lower()
            if key and key not in seen:
                seen.add(key)
                unique.append(q)

        final = unique[:num_questions]

        # Store in cache for future identical requests
        await cache.set(cache_key, final, ttl=settings.cache_ttl_seconds)
        logger.info(f"Cached {len(final)} questions (ttl={settings.cache_ttl_seconds}s)")

        return final

    # ------------------------------------------------------------------
    # Quiz lifecycle — dual-path: in-memory (default) or PostgreSQL
    # Controlled by settings.use_database. The router passes db=None
    # when use_database=False.
    # ------------------------------------------------------------------

    async def create_quiz(
        self,
        questions: list[dict],
        db: "AsyncSession | None" = None,
        source_type: str = "topic",
        topic: str | None = None,
        document_id: str | None = None,
    ) -> str:
        if db is not None:
            return await self._create_quiz_db(questions, db, source_type, topic, document_id)
        return self._create_quiz_memory(questions)

    def _create_quiz_memory(self, questions: list[dict]) -> str:
        quiz_id = str(uuid.uuid4())
        self.quizzes[quiz_id] = {
            "questions": {q["id"]: q for q in questions},
            "answers": {},
        }
        return quiz_id

    async def _create_quiz_db(
        self,
        questions: list[dict],
        db: "AsyncSession",
        source_type: str,
        topic: str | None,
        document_id: str | None,
    ) -> str:
        from app.db_models import Quiz, Question as QuestionModel

        quiz_id = uuid.uuid4()
        quiz_row = Quiz(
            id=quiz_id,
            source_type=source_type,
            topic=topic,
            document_id=uuid.UUID(document_id) if document_id else None,
        )
        db.add(quiz_row)
        await db.flush()  # get quiz_id into DB without committing

        for q in questions:
            db.add(QuestionModel(
                id=uuid.UUID(q["id"]),
                quiz_id=quiz_id,
                type=q["type"],
                question_text=q["question"],
                options=q.get("options"),
                correct_answer=q["correct_answer"],
                explanation=q.get("explanation", ""),
                difficulty=q.get("difficulty", "medium"),
                source_chunk=q.get("source_chunk"),
            ))
        # Session commits in the router's get_db() dependency
        logger.info(f"Quiz {quiz_id} persisted to DB with {len(questions)} questions")
        return str(quiz_id)

    async def get_quiz(
        self, quiz_id: str, db: "AsyncSession | None" = None
    ) -> dict | None:
        if db is not None:
            return await self._get_quiz_db(quiz_id, db)
        return self.quizzes.get(quiz_id)

    async def _get_quiz_db(
        self, quiz_id: str, db: "AsyncSession"
    ) -> dict | None:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db_models import Quiz, Answer

        # Expire all cached ORM objects so selectinload fetches fresh data from the DB.
        # Without this, Question rows loaded during create_quiz have stale (empty)
        # answer relationship state in the identity map.
        await db.flush()
        db.expire_all()

        stmt = (
            select(Quiz)
            .where(Quiz.id == uuid.UUID(quiz_id))
            .options(selectinload(Quiz.questions).selectinload(
                __import__("app.db_models", fromlist=["Question"]).Question.answer
            ))
        )
        result = await db.execute(stmt)
        quiz_row = result.scalar_one_or_none()
        if quiz_row is None:
            return None

        questions_dict: dict[str, dict] = {}
        answers_dict: dict[str, dict] = {}
        for q in quiz_row.questions:
            q_dict = {
                "id": str(q.id),
                "type": q.type,
                "question": q.question_text,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
                "difficulty": q.difficulty,
                "source_chunk": q.source_chunk,
            }
            questions_dict[str(q.id)] = q_dict
            if q.answer is not None:
                answers_dict[str(q.id)] = {
                    "user_answer": q.answer.user_answer,
                    "is_correct": q.answer.is_correct,
                    "score": q.answer.score,
                    "feedback": q.answer.feedback,
                    "correct_answer": q.correct_answer,
                }
        return {"questions": questions_dict, "answers": answers_dict}

    async def save_answer(
        self,
        question_id: str,
        answer_data: dict,
        db: "AsyncSession | None" = None,
    ) -> None:
        """Persist an answer row (DB path only — in-memory path stores in quiz dict directly)."""
        if db is None:
            return
        from app.db_models import Answer

        # Upsert: delete existing answer for this question if any, then insert
        from sqlalchemy import select, delete
        await db.execute(
            delete(Answer).where(Answer.question_id == uuid.UUID(question_id))
        )
        db.add(Answer(
            id=uuid.uuid4(),
            question_id=uuid.UUID(question_id),
            user_answer=answer_data["user_answer"],
            is_correct=answer_data["is_correct"],
            score=answer_data["score"],
            feedback=answer_data.get("feedback", ""),
        ))
        await db.flush()  # make the new row visible in this session's identity map

    async def grade_answer(self, question: dict, user_answer: str) -> dict:
        q_type = question["type"]
        correct = question["correct_answer"]

        if q_type in ("mcq", "true_false"):
            user_norm = user_answer.strip().lower()
            correct_norm = correct.strip().lower()

            is_correct = (
                user_norm == correct_norm
                or user_norm in correct_norm
                or correct_norm in user_norm
            )

            return {
                "is_correct": is_correct,
                "score": 1.0 if is_correct else 0.0,
                "feedback": question["explanation"] if is_correct else f"The correct answer is: {correct}. {question['explanation']}",
                "correct_answer": correct,
            }
        else:
            # Short answer — use LLM
            prompt = GRADING_USER.format(
                question=question["question"].replace("{", "{{").replace("}", "}}"),
                correct_answer=correct.replace("{", "{{").replace("}", "}}"),
                user_answer=user_answer.replace("{", "{{").replace("}", "}}"),
            )
            try:
                result = await llm_service.generate_json(prompt, GRADING_SYSTEM, temperature=0.3)
                return {
                    "is_correct": result.get("is_correct", False),
                    "score": float(result.get("score", 0)),
                    "feedback": result.get("feedback", question["explanation"]),
                    "correct_answer": correct,
                }
            except Exception:
                is_correct = user_answer.strip().lower() == correct.strip().lower()
                return {
                    "is_correct": is_correct,
                    "score": 1.0 if is_correct else 0.0,
                    "feedback": question["explanation"],
                    "correct_answer": correct,
                }

    async def generate_quiz_summary(self, questions: list[dict], user_answers: list[dict]) -> dict:
        total = len(questions)
        correct_count = sum(1 for a in user_answers if a.get("is_correct"))
        percentage = (correct_count / total * 100) if total > 0 else 0

        per_type: dict[str, dict] = {}
        for q, a in zip(questions, user_answers):
            qt = q["type"]
            if qt not in per_type:
                per_type[qt] = {"correct": 0, "total": 0}
            per_type[qt]["total"] += 1
            if a.get("is_correct"):
                per_type[qt]["correct"] += 1

        per_type_summary = "\n".join(
            f"- {t}: {d['correct']}/{d['total']} correct"
            for t, d in per_type.items()
        )

        wrong_questions = "\n".join(
            f"- Q: {q['question']} (Their answer: {a.get('user_answer', 'N/A')}, Correct: {q['correct_answer']})"
            for q, a in zip(questions, user_answers)
            if not a.get("is_correct")
        ) or "None - perfect score!"

        questions_with_results = []
        for q, a in zip(questions, user_answers):
            questions_with_results.append({
                **q,
                "user_answer": a.get("user_answer", ""),
                "is_correct": a.get("is_correct", False),
                "score": a.get("score", 0),
                "feedback": a.get("feedback", ""),
            })

        try:
            prompt = SUMMARY_USER.format(
                score=correct_count,
                total=total,
                percentage=percentage,
                per_type_summary=per_type_summary,
                wrong_questions=wrong_questions,
            )
            summary = await llm_service.generate_json(prompt, SUMMARY_SYSTEM, temperature=0.7)
            coaching_message = summary.get("coaching_message", "Great effort! Keep studying to improve.")
            weak_areas = summary.get("weak_areas", [])
        except Exception:
            coaching_message = f"You scored {correct_count}/{total} ({percentage:.0f}%). Keep practicing to improve!"
            weak_areas = []

        return {
            "score": correct_count,
            "total": total,
            "percentage": round(percentage, 1),
            "per_type": {t: f"{d['correct']}/{d['total']}" for t, d in per_type.items()},
            "coaching_message": coaching_message,
            "weak_areas": weak_areas,
            "questions_with_results": questions_with_results,
        }


quiz_service = QuizService()
