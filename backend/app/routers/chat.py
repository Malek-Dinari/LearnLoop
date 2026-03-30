from fastapi import APIRouter

from app.models import CoachRequest, CoachResponse
from app.services.chat_service import chat_service

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
