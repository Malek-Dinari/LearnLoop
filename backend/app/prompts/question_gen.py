DOCUMENT_QUESTION_SYSTEM = (
    "You are an expert educator creating quiz questions. You create clear, "
    "unambiguous questions that test understanding, not just memorization. "
    "Every question MUST be answerable from the provided text."
)

DOCUMENT_QUESTION_USER = """Based on the following text, generate {num_questions} quiz questions.

TEXT:
---
{content}
---

Generate a mix of question types as specified: {question_types_description}

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
    "to application and analysis."
)

TOPIC_QUESTION_USER = """Generate {num_questions} quiz questions about the topic: "{topic}"

Generate a mix: {question_types_description}

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
