import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import FlashcardGenerateRequest, FlashcardGenerateResponse
from app.services.flashcard_service import flashcard_service
from app.services.document_service import document_service
from app.services.quiz_service import quiz_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/flashcards", tags=["flashcards"])


@router.post("/generate", response_model=FlashcardGenerateResponse)
async def generate_flashcards(
    request: FlashcardGenerateRequest,
    db: AsyncSession | None = Depends(get_db),
):
    num_cards = max(1, min(request.num_cards, 30))

    if request.source_type == "quiz":
        if not request.quiz_id:
            raise HTTPException(400, "quiz_id required for quiz-based flashcards")
        quiz = await quiz_service.get_quiz(request.quiz_id, db)
        if not quiz:
            raise HTTPException(404, "Quiz not found")
        questions_with_results = [
            {
                **q,
                **quiz["answers"].get(q["id"], {"user_answer": "", "is_correct": True, "score": 1}),
            }
            for q in quiz["questions"].values()
        ]
        cards = await flashcard_service.generate_from_quiz(questions_with_results, num_cards)

    elif request.source_type == "document":
        if not request.document_id:
            raise HTTPException(400, "document_id required for document-based flashcards")
        doc = await document_service.get_document(request.document_id, db)
        if not doc:
            raise HTTPException(404, "Document not found")
        cards = await flashcard_service.generate_from_document(doc["chunks"], num_cards)

    else:
        raise HTTPException(400, "source_type must be 'quiz' or 'document'")

    if not cards:
        raise HTTPException(502, "Flashcard generation failed — LLM returned no cards")

    return FlashcardGenerateResponse(flashcards=cards)
