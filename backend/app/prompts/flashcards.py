FLASHCARD_SYSTEM = (
    "You are an expert educator creating concise, high-quality study flashcards. "
    "Each flashcard must have a clear question on the front and a concise answer on the back. "
    "Focus on the most important concepts. "
    "You MUST respond with ONLY a valid JSON array — no markdown, no code fences, no prose."
)

# Each question entry carries its ID so the model echoes it back in the output.
# This lets the frontend show "From Q3" badges and sort by wrong-first.
FLASHCARD_FROM_QUIZ_USER = """A student just completed a quiz. Generate {num_cards} flashcards to help them study.

Prioritize questions they got WRONG — those are listed first with a ✗ marker.

Questions (each has an id — echo it in your output):
{questions_with_ids}

Rules:
- Each flashcard rephrases the CONCEPT tested by that question (not just repeats the question verbatim)
- Front: a short, clear study prompt
- Back: a concise answer (1-3 sentences max)
- Category: the topic area (e.g. "Photosynthesis", "French Revolution")
- question_id: copy the id field from the question this card is based on (string, not null)

Respond with ONLY a JSON array, one object per flashcard:
[{{"front": "...", "back": "...", "category": "...", "question_id": "..."}}]"""

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
