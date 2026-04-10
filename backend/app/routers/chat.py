from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CoachRequest, CoachResponse, StudyChatRequest, StudyChatResponse
from app.services.chat_service import chat_service
from app.services.quiz_service import quiz_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/coach", response_model=CoachResponse)
async def coach(request: CoachRequest):
    response = await chat_service.coach(
        question=request.question,
        user_answer=request.user_answer,
        conversation=request.conversation,
        user_message=request.message,
    )
    return CoachResponse(response=response)


@router.post("/study", response_model=StudyChatResponse)
async def study_chat(
    request: StudyChatRequest,
    db: AsyncSession | None = Depends(get_db),
):
    quiz_summary = None
    if request.quiz_id:
        quiz = await quiz_service.get_quiz(request.quiz_id, db)
        if quiz:
            # Build a lightweight summary from cached answers
            questions = list(quiz["questions"].values())
            answers = quiz["answers"]
            correct = sum(1 for q in questions if answers.get(q["id"], {}).get("is_correct", False))
            total = len(questions)
            pct = (correct / total * 100) if total else 0
            weak_areas = [
                q["question"][:60]
                for q in questions
                if not answers.get(q["id"], {}).get("is_correct", True)
            ][:3]
            quiz_summary = {
                "score": correct,
                "total": total,
                "percentage": pct,
                "weak_areas": weak_areas,
            }

    response = await chat_service.study_chat(
        context=request.context,
        conversation=request.conversation,
        user_message=request.message,
        quiz_summary=quiz_summary,
    )
    return StudyChatResponse(response=response)
