import uuid

from app.prompts.question_gen import (
    DOCUMENT_QUESTION_SYSTEM,
    DOCUMENT_QUESTION_USER,
    TOPIC_QUESTION_SYSTEM,
    TOPIC_QUESTION_USER,
)
from app.prompts.grading import GRADING_SYSTEM, GRADING_USER, SUMMARY_SYSTEM, SUMMARY_USER
from app.services.llm_service import llm_service


def _question_types_description(types: list[str]) -> str:
    mapping = {
        "mcq": "Multiple Choice (4 options, one correct)",
        "true_false": "True/False",
        "short_answer": "Short Answer",
    }
    return ", ".join(mapping.get(t, t) for t in types)


class QuizService:
    def __init__(self):
        # quiz_id -> {questions, answers}
        self.quizzes: dict[str, dict] = {}

    async def generate_questions(
        self,
        content: str,
        source_type: str,
        num_questions: int = 10,
        question_types: list[str] | None = None,
    ) -> list[dict]:
        if question_types is None:
            question_types = ["mcq", "true_false", "short_answer"]

        types_desc = _question_types_description(question_types)

        if source_type == "topic":
            system = TOPIC_QUESTION_SYSTEM
            # Escape any braces in topic text before .format()
            safe_content = content.replace("{", "{{").replace("}", "}}")
            user = TOPIC_QUESTION_USER.format(
                num_questions=num_questions,
                topic=safe_content,
                question_types_description=types_desc,
            )
        else:
            system = DOCUMENT_QUESTION_SYSTEM
            # Escape braces in document content to prevent .format() errors
            safe_content = content[:4000].replace("{", "{{").replace("}", "}}")
            user = DOCUMENT_QUESTION_USER.format(
                num_questions=num_questions,
                content=safe_content,
                question_types_description=types_desc,
            )

        raw_questions = await llm_service.generate_json(user, system, temperature=0.3)

        if isinstance(raw_questions, dict) and "questions" in raw_questions:
            raw_questions = raw_questions["questions"]

        questions = []
        for q in raw_questions[:num_questions]:
            # Validate and normalize
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

            # Ensure T/F has proper options
            if q_type == "true_false" and not question["options"]:
                question["options"] = ["True", "False"]

            # Ensure MCQ has options
            if q_type == "mcq" and not question["options"]:
                q_type = "short_answer"
                question["type"] = "short_answer"

            questions.append(question)

        return questions

    def create_quiz(self, questions: list[dict]) -> str:
        quiz_id = str(uuid.uuid4())
        self.quizzes[quiz_id] = {
            "questions": {q["id"]: q for q in questions},
            "answers": {},
        }
        return quiz_id

    def get_quiz(self, quiz_id: str) -> dict | None:
        return self.quizzes.get(quiz_id)

    async def grade_answer(self, question: dict, user_answer: str) -> dict:
        q_type = question["type"]
        correct = question["correct_answer"]

        if q_type in ("mcq", "true_false"):
            # Normalize for comparison
            user_norm = user_answer.strip().lower()
            correct_norm = correct.strip().lower()

            # Handle "A) answer" format - check both full match and letter prefix
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
            # Short answer - use LLM
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
                # Fallback to simple comparison
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
