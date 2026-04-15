DOCUMENT_QUESTION_SYSTEM = (
    "You are an expert educator creating quiz questions. You create clear, "
    "unambiguous questions that test understanding, not just memorization. "
    "Every question MUST be answerable from the provided text. "
    "Ensure each question is unique and tests a different concept."
)

DOCUMENT_QUESTION_USER = """Based on the following text, generate {num_questions} quiz questions.

TEXT:
---
{content}
---

Generate a mix of question types as specified: {question_types_description}

{diversity_directive}

For each question, provide:
- A clear, specific question
- The correct answer
- A brief explanation of why the answer is correct
- A difficulty rating (easy/medium/hard)

For multiple choice: provide exactly 4 options where only one is correct. Distractors should be plausible but clearly wrong.

Respond with ONLY a JSON array. No other text. No markdown fences.
Each element:
{{
  "type": "mcq" | "true_false" | "short_answer",
  "question": "...",
  "options": ["A) ...", "B) ...", "C) ...", "D) ..."] or ["True", "False"] or null,
  "correct_answer": "the correct option text or answer",
  "explanation": "why this is correct",
  "difficulty": "easy" | "medium" | "hard"
}}"""

TOPIC_QUESTION_SYSTEM = (
    "You are an expert educator. Create quiz questions about the given topic "
    "that test genuine understanding. Questions should range from basic recall "
    "to application and analysis. "
    "Ensure each question is unique and tests a different concept."
)

TOPIC_QUESTION_USER = """Generate {num_questions} quiz questions about the topic: "{topic}"

Generate a mix: {question_types_description}

{diversity_directive}

Cover different aspects and subtopics within "{topic}".
Range difficulty from easy to hard.

Respond with ONLY a JSON array. No other text. No markdown fences.
Each element:
{{
  "type": "mcq" | "true_false" | "short_answer",
  "question": "...",
  "options": ["A) ...", "B) ...", "C) ...", "D) ..."] or ["True", "False"] or null,
  "correct_answer": "the correct option text or answer",
  "explanation": "why this is correct",
  "difficulty": "easy" | "medium" | "hard"
}}"""


# Aspects cycled across batches to force coverage breadth
QUESTION_ASPECTS = [
    "definition/terminology",
    "application/use-case",
    "comparison/contrast",
    "cause-and-effect",
    "analysis/evaluation",
]


def build_diversity_directive(batch_index: int, seen_topics: list[str] | None = None) -> str:
    """Construct a per-batch diversity directive.

    - Rotates through QUESTION_ASPECTS to force breadth across batches.
    - If seen_topics is non-empty, tells the model to avoid repeating them.
    """
    parts: list[str] = []
    aspect = QUESTION_ASPECTS[batch_index % len(QUESTION_ASPECTS)]
    parts.append(f"Focus this batch on questions that test {aspect}.")
    if seen_topics:
        # Truncate long lists to stay within a reasonable prompt size
        topic_list = ", ".join(seen_topics[:12])
        parts.append(
            f"Avoid repeating these concepts already covered: {topic_list}."
        )
    return " ".join(parts)
