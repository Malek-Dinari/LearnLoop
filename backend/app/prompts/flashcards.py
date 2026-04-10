FLASHCARD_SYSTEM = (
    "You are an expert educator creating concise, high-quality study flashcards. "
    "Each flashcard must have a clear question on the front and a concise answer on the back. "
    "Focus on the most important concepts. "
    "You MUST respond with ONLY a valid JSON array — no markdown, no code fences, no prose."
)

FLASHCARD_FROM_QUIZ_USER = """A student just completed a quiz. Here are the questions they got WRONG or partially correct.
Generate {num_cards} flashcards to help them study these weak areas.

Wrong/missed questions:
{wrong_questions}

All questions for context:
{all_questions}

Rules:
- Prioritize concepts from wrong answers
- Front: a short, clear question or prompt
- Back: a concise answer (1-3 sentences max)
- Category: the topic area (e.g. "Photosynthesis", "French Revolution")

Respond with ONLY a JSON array like:
[{{"front": "...", "back": "...", "category": "..."}}]"""

FLASHCARD_FROM_DOCUMENT_USER = """Based on this study material, generate {num_cards} flashcards covering the key concepts.

Material:
{content}

Rules:
- Cover the most important facts, definitions, and relationships
- Front: a short question or fill-in-the-blank prompt
- Back: a concise answer (1-3 sentences max)
- Category: the topic area (infer from content)

Respond with ONLY a JSON array like:
[{{"front": "...", "back": "...", "category": "..."}}]"""
